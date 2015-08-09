# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys, time
import subprocess
from queue import Queue
import asyncio

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtMultimedia import *

from widgets.login_dialog import LoginDialog
from widgets.trayicon import TrayIcon
from widgets.music_table_widget import MusicTableWidget
from widgets.lyric_widget import LyricWidget
from widgets.playlist_widget import PlaylistWidget, PlaylistItem

from views import UiMainWidget

from plugin import NetEaseMusic

from base.models import DataModel
from base.player import Player
from base.network_manger import NetworkManager
from base.logger import LOG

from base import common

from base.common import func_coroutine, singleton

from constants import WINDOW_ICON


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        # QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()    # 那些widget对象都通过self.ui.*.*来访问，感觉也不是很好
        self.ui.setup_ui(self)

        self.player = Player()

        self.current_playlist_widget = MusicTableWidget()
        self.lyric_widget = LyricWidget(self)

        self.left_central_widget = self.ui.left_widget.central_widget

        self.status = self.ui.status
        self.trayicon = TrayIcon(self)
        self.webview = self.ui.right_widget.webview     # 常用的对象复制一下，方便使用
        self.progress = self.ui.progress_info
        self.network_manger = NetworkManager()

        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)

        self.play_or_pause_btn = self.ui.top_widget.play_pause_btn

        self.api = None
        self.network_queue = Queue()

        self.init()

        self.state = {'is_login': False,
                      'current_mid': 0,
                      'current_pid': 0}

        APP_EVENT_LOOP = asyncio.get_event_loop()
        APP_EVENT_LOOP.call_later(1, self._init_plugins)

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.y
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def _init_plugins(self):
        NetEaseMusic.init(self)

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        self.trayicon.showMessage(u"提示",
                                  u'程序已最小化到托盘，点击托盘可以进行操作')

    def init(self):
        self.setWindowIcon(QIcon(WINDOW_ICON))
        self.setWindowTitle('FeelUOwn')
        self.trayicon.show()
        self.init_signal_binding()
        self.init_widgets()
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.resize(960, 580)

    def init_signal_binding(self):
        """初始化部分信号绑定
        :return:
        """
        self.ui.top_widget.login_btn.clicked.connect(self.pop_login)
        self.ui.top_widget.last_music_btn.clicked.connect(self.last_music)
        self.ui.top_widget.next_music_btn.clicked.connect(self.next_music)
        self.ui.top_widget.slider_play.sliderMoved.connect(self.seek)
        self.ui.top_widget.show_current_list.clicked.connect(self.show_current_playlist)

        self.ui.top_widget.search_edit.returnPressed.connect(self.search_music)
        self.ui.top_widget.add_to_favorite.clicked.connect(self.set_favorite)
        self.ui.top_widget.play_mv_btn.clicked.connect(self.play_song_mv)
        self.ui.top_widget.show_lyric_btn.clicked.connect(self.show_hide_lyric)

        self.left_central_widget.create_fold_spread_btn.clicked.connect(
            self.ui.left_widget.central_widget.create_list_widget.fold_spread_with_animation)
        self.left_central_widget.collection_fold_spread_btn.clicked.connect(
            self.ui.left_widget.central_widget.collection_list_widget.fold_spread_with_animation)
        self.left_central_widget.local_fold_spread_btn.clicked.connect(
            self.ui.left_widget.central_widget.local_list_widget.fold_spread_with_animation)


        self.current_playlist_widget.signal_play_music.connect(self.play)
        self.current_playlist_widget.signal_remove_music_from_list.connect(self.remove_music_from_list)

        self.play_or_pause_btn.clicked.connect(self.play_or_pause)

        self.webview.loadProgress.connect(self.on_webview_progress)
        self.webview.signal_play.connect(self.play)
        self.webview.signal_play_songs.connect(self.play_songs)
        self.webview.signal_search_artist.connect(self.search_artist)
        self.webview.signal_search_album.connect(self.search_album)
        self.webview.signal_play_mv.connect(self.play_mv)

        self.player.signal_player_media_changed.connect(self.on_player_media_changed)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.player.stateChanged.connect(self.trayicon.on_player_state_changed)
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)
        self.player.signal_playlist_is_empty.connect(self.on_playlist_empty)
        self.player.signal_playback_mode_changed.connect(self.on_playback_mode_changed)
        self.player.signal_player_error.connect(self.on_player_error_occured)

        self.network_manger.finished.connect(self.access_network_queue)

        self.search_shortcut.activated.connect(self.set_search_focus)

    def init_widgets(self):
        self.current_playlist_widget.resize(500, 200)
        self.current_playlist_widget.close()
        self.progress.setRange(0, 100)

        self.shadow_effect = QGraphicsDropShadowEffect(self.progress)
        self.shadow_effect.setColor(QColor("red"))
        # self._shadow_effect.setYOffset(2)
        self.shadow_effect.setBlurRadius(10)
        self.progress.setGraphicsEffect(self.shadow_effect)

    """这部分写一些工具
    """
    def is_response_ok(self, data):
        """check response status code
        """
        if not isinstance(data, dict):
            return True

        if data['code'] == 200:
            return True

        self.show_network_error_message()
        return False

    def show_network_error_message(self, text="异常: 网络或者远程服务器变动"):
        self.status.showMessage(text, 3000)

    """这部分写一些交互逻辑
    """
    @func_coroutine
    def set_user(self, data):
        avatar_url = data['avatar']
        request = QNetworkRequest(QUrl(avatar_url))
        self.network_manger.get(request)
        self.network_queue.put(self.show_avatar)
        self.show_user_playlist()

    def set_login(self):
        self.state['is_login'] = True
        self.ui.top_widget.add_to_favorite.show()
        self.ui.top_widget.login_btn.hide()

    @func_coroutine
    def show_user_playlist(self):
        while self.ui.left_widget.central_widget.create_list_widget.layout.takeAt(0):
            item = self.ui.left_widget.central_widget.create_list_widget.layout.takeAt(0)
            del item
        while self.ui.left_widget.central_widget.collection_list_widget.layout.takeAt(0):
            item = self.ui.left_widget.central_widget.create_list_widget.layout.takeAt(0)
            del item

        playlists = self.api.get_user_playlist()
        if not self.is_response_ok(playlists):
            self.show_network_error_message()
            return

        for playlist in playlists:

            # self.status.showMessage(u'正在缓存您的歌单列表', 10000)  # 会让程序整体等待10s
            pid = playlist['id']

            w = PlaylistItem(self)
            w.set_playlist_item(playlist)

            # 感觉这句话增加了耦合度, 暂时没找到好的解决办法
            w.signal_text_btn_clicked.connect(self.on_playlist_btn_clicked)

            if self.api.is_playlist_mine(playlist):
                self.ui.left_widget.central_widget.create_list_widget.layout.addWidget(w)
                if pid == self.api.favorite_pid:
                    @func_coroutine
                    def load_favorite_playlist():
                        favorite_playlist_detail = self.api.get_playlist_detail(pid)
                        self.webview.load_playlist(favorite_playlist_detail)
                    load_favorite_playlist()
                else:
                    APP_EVENT_LOOP = asyncio.get_event_loop()
                    APP_EVENT_LOOP.call_soon(self.api.get_playlist_detail, pid)
            else:
                self.ui.left_widget.central_widget.collection_list_widget.layout.addWidget(w)

    def show_avatar(self, res):
        """界面改版之后再使用
        :param res:
        :return:
        """
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        if self.state['is_login']:
            self.ui.top_widget.login_btn.close()
        self.ui.top_widget.login_label.show()

        self.ui.top_widget.login_label.setPixmap(pixmap.scaled(55, 55, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def set_music_icon(self, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        self.ui.top_widget.img_label.setPixmap(pixmap.scaled(self.ui.top_widget.img_label.size(),
                                                             Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.setWindowIcon(QIcon(pixmap))

    def show_current_playlist(self):
        self.current_playlist_widget.resize(500, 200)
        if self.current_playlist_widget.isVisible():
            self.current_playlist_widget.hide()

        width = self.current_playlist_widget.width()
        height = self.current_playlist_widget.height()
        p_width = self.width()

        geometry = self.geometry()
        p_x, p_y = geometry.x(), geometry.y()

        x = p_x + p_width - width
        y = self.ui.top_widget.height() + p_y - 8

        self.current_playlist_widget.setGeometry(x, y, 500, 300)
        self.current_playlist_widget.show()
        self.current_playlist_widget.setFocus(True)

    def judge_favorite(self, mid):
        if self.api.is_favorite_music(mid):
            self.ui.top_widget.add_to_favorite.setChecked(True)
        else:
            self.ui.top_widget.add_to_favorite.setChecked(False)

    @func_coroutine
    @pyqtSlot(bool)
    def set_favorite(self, checked=True):
        data = self.api.set_music_to_favorite(self.state['current_mid'], checked)
        if not self.is_response_ok(data):
            self.ui.top_widget.add_to_favorite.setChecked(not checked)
            return False
        playlist_detail = self.api.get_playlist_detail(self.api.favorite_pid, cache=False)
        if not playlist_detail:
            return False
        if self.state['current_pid'] == self.api.favorite_pid:
            self.webview.load_playlist(playlist_detail)
        return True


    """某些操作
    """
    @pyqtSlot(QNetworkReply)
    def access_network_queue(self, res):
        if self.network_queue.empty():
            LOG.info('Nothing in network queue')
            return
        item = self.network_queue.get_nowait()
        item(res)

    """这部分写 pyqtSlot
    """

    @pyqtSlot(int)
    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    @pyqtSlot()
    def pop_login(self):
        if self.state['is_login'] is False:
            w = LoginDialog(self)
            w.signal_login_sucess.connect(self.on_login_success)
            w.show()

    @pyqtSlot()
    def last_music(self):
        self.player.play_last()

    @pyqtSlot()
    def next_music(self):
        self.player.play_next()

    @pyqtSlot()
    def play_or_pause(self):
        if self.player.mediaStatus() == QMediaPlayer.NoMedia or \
                self.player.mediaStatus() == QMediaPlayer.UnknownMediaStatus:
            self.play_or_pause_btn.setChecked(True)     # 暂停状态
            return
        self.player.play_or_pause()

    @pyqtSlot(int)
    def on_player_position_changed(self, ms):
        time_text = QTime(0, (ms / 60000) % 60, (ms / 1000) % 60)
        self.ui.top_widget.time_lcd.setText(time_text.toString("mm:ss"))
        self.ui.top_widget.slider_play.setValue(ms / 1000)

        if self.lyric_widget.isVisible():
            if self.lyric_widget.has_lyric():
                self.lyric_widget.sync_lyric(ms)
            else:
                lyric_model = self.api.get_lyric_detail(self.state['current_mid'])
                if not self.is_response_ok(lyric_model):
                    return

                if lyric_model:
                    self.lyric_widget.set_lyric(lyric_model)
                    self.lyric_widget.sync_lyric(ms)
                else:
                    self.lyric_widget.setText(u'歌曲没有歌词')

    @pyqtSlot(dict)
    def on_login_success(self, data):
        """
        登陆成功
        :param data:
        :return:
        """
        self.set_login()
        self.set_user(data)

    @func_coroutine
    @pyqtSlot(int)
    def on_playlist_btn_clicked(self, pid):
        playlist_detail = self.api.get_playlist_detail(pid)
        if not self.is_response_ok(playlist_detail):
            return
        self.webview.load_playlist(playlist_detail)
        self.state['current_pid'] = pid

    @pyqtSlot(int)
    def on_webview_progress(self, percent):
        self.progress.setValue(percent)

    @func_coroutine
    @pyqtSlot(int)
    def play(self, mid=None):
        songs = self.api.get_song_detail(mid)
        if not self.is_response_ok(songs):
            return

        if len(songs) == 0:
            self.status.showMessage(u'这首音乐在地震中消失了', 4000)
            return
        self.player.play(songs[0])

    @func_coroutine
    @pyqtSlot(int)
    def play_mv(self, mvid):

        mv_model = self.api.get_mv_detail(mvid)
        if not self.is_response_ok(mv_model):
            return

        url_high = mv_model['url_high']
        url_middle = mv_model['url_middle']
        clipboard = QApplication.clipboard()
        clipboard.setText(url_high)

        if common.judge_system().lower() == 'Linux'.lower():
            if common.judge_platform()[-3].lower() == 'deepin':
                self.player.pause()
                self.status.showMessage(u"准备调用 deepin-movie 播放器播放mv...", 5000)
                subprocess.Popen(['deepin-movie', url_high])
            elif common.judge_platform()[-3].lower() == 'ubuntu':
                self.player.pause()
                self.status.showMessage(u"你的系统是Ubuntu，准备调用 vlc 播放器播放mv...", 5000)
                subprocess.Popen(['vlc', url_high, '--play-and-exit', '-f'])
            else:
                self.player.pause()
                self.status.showMessage(u"准备调用 vlc 播放器播放mv...", 5000)
                subprocess.Popen(['vlc', url_high, '--play-and-exit', '-f'])
        elif common.judge_system().lower() == 'Darwin'.lower():
            self.player.pause()
            self.status.showMessage(u"准备调用 QuickTime Player 播放mv", 4000)
            subprocess.Popen(['open', '-a', 'QuickTime Player', url_high])
        else:
            self.status.showMessage(u"您的系统不是Linux。程序已经将视频的播放地址复制到剪切板，你可以使用你喜欢的播放器播放视频", 5000)
            # self.webview.load_mv(mv_model)

    @func_coroutine
    def play_song_mv(self):
        mid = self.state['current_mid']
        data = self.api.get_song_detail(mid)
        if not self.is_response_ok(data):
            return
        music_model = data[0]

        mvid = music_model['mvid']
        self.play_mv(int(mvid))

    def show_hide_lyric(self):
        if self.lyric_widget.isVisible():
            self.lyric_widget.hide()
        else:
            self.lyric_widget.show()

    @pyqtSlot(int)
    def play_songs(self, songs):
        if len(songs) == 0:
            self.status.showMessage(u'该列表没有歌曲', 2000)
            return
        self.current_playlist_widget.set_songs(songs)
        self.player.set_music_list(songs)

    @func_coroutine
    @pyqtSlot(int)
    def search_artist(self, aid):
        artist_detail_model = self.api.get_artist_detail(aid)
        if not self.is_response_ok(artist_detail_model):
            return
        self.webview.load_artist(artist_detail_model)
        self.state['current_pid'] = 0

    @func_coroutine
    @pyqtSlot(int)
    def search_album(self, aid):
        album_detail_model = self.api.get_album_detail(aid)
        if not self.is_response_ok(album_detail_model):
            return
        self.webview.load_album(album_detail_model)
        self.state['current_pid'] = 0

    @pyqtSlot(dict)
    def on_player_media_changed(self, music_model):
        self.player.stop()
        self.player.play()
        artists = music_model['artists']
        artists_name = ''
        for artist in artists:
            artists_name += artist['name']
        title = music_model['name'] + ' - ' + artists_name
        self.setWindowTitle(title)
        
        metrics = QFontMetrics(self.ui.top_widget.font())
        title = metrics.elidedText(title, Qt.ElideRight, 300 - 40)
        self.ui.top_widget.text_label.setText(title)
        self.lyric_widget.reset_lyric()

        self.ui.top_widget.time_lcd.setText('00:00')
        self.ui.top_widget.slider_play.setRange(0, self.player.duration() / 1000)

        self.network_manger.get(QNetworkRequest(QUrl(music_model['album']['picUrl']+"?param=55y55")))
        self.network_queue.put(self.set_music_icon)    # 更换任务栏图标

        self.current_playlist_widget.add_item_from_model(music_model)
        self.current_playlist_widget.focus_cell_by_mid(music_model['id'])

        self.trayicon.showMessage(u'正在播放: ', music_model['name'])

        self.state['current_mid'] = music_model['id']

        self.judge_song_has_mv(music_model)
        if self.state['is_login']:
            self.judge_favorite(music_model['id'])

    def judge_song_has_mv(self, music_model):
        if music_model['mvid'] != 0:
            self.ui.top_widget.play_mv_btn.show()
            return
        self.ui.top_widget.play_mv_btn.close()


    @pyqtSlot(int)
    def on_player_duration_changed(self, duration):
        self.ui.top_widget.slider_play.setRange(0, self.player.duration() / 1000)

    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_or_pause_btn.setChecked(False)
        else:
            self.play_or_pause_btn.setChecked(True)

    @pyqtSlot(int)
    def remove_music_from_list(self, mid):
        self.player.remove_music(mid)

    @pyqtSlot()
    def on_playlist_empty(self):
        self.ui.top_widget.text_label.setText(u'当前没有歌曲播放')
        self.ui.top_widget.time_lcd.setText('00:00')
        self.ui.top_widget.play_pause_btn.setChecked(True)

    @pyqtSlot()
    def set_search_focus(self):
        self.ui.top_widget.search_edit.setFocus()

    @func_coroutine
    @pyqtSlot()
    def search_music(self):
        text = self.ui.top_widget.search_edit.text()
        if text != '':
            self.status.showMessage(u'正在搜索: ' + text)
            songs = self.api.search(text)
            if not self.is_response_ok(songs):
                return
            PlaylistItem.de_active_all()
            self.webview.load_search_result(songs)
            self.state['current_pid'] = 0
            length = len(songs)
            if length != 0:
                self.status.showMessage(u'搜索到 ' + str(length) + u' 首 ' + text + u' 相关歌曲', 5000)
                return
            else:
                self.ui.status.showMessage(u'很抱歉，没有找到相关歌曲', 5000)
                return

    @pyqtSlot(int)
    def on_web_load_progress(self, progress):
        QApplication.processEvents()
        self.progress.setValue(progress)

    @pyqtSlot(QMediaPlaylist.PlaybackMode)
    def on_playback_mode_changed(self, playback_mode):
        if playback_mode == 0:
            self.trayicon.showMessage(u"通知", u"切换到单曲播放模式")
        elif playback_mode == 1:
            self.trayicon.showMessage(u"通知", u"切换到单曲循环模式")
        elif playback_mode == 2:
            self.trayicon.showMessage(u"通知", u"切换到顺序播放模式")
        elif playback_mode == 3:
            self.trayicon.showMessage(u"通知", u"切换到全部循环模式")
        elif playback_mode == 4:
            self.trayicon.showMessage(u"通知", u"切换到随机播放模式")

    @pyqtSlot(str)
    def on_player_error_occured(self, message):
        self.trayicon.showMessage(u'播放器错误', message, QSystemTrayIcon.Warning)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
