# -*- coding:utf8 -*-

import sys
import subprocess
from queue import Queue
import asyncio
import platform

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtMultimedia import *

from interfaces import ControllerApi, ViewApi
from widgets.login_dialog import LoginDialog
from widgets.music_table import MusicTableWidget
from widgets.lyric import LyricWidget
from widgets.playlist import PlaylistItem
from widgets.desktop_mini import DesktopMiniLayer
from widgets.notify import NotifyWidget
from views import UiMainWidget
from plugin import NetEaseMusic, Hotkey
from base.player import Player
from base.network_manger import NetworkManager
from base.logger import LOG
from base.utils import func_coroutine
from base.models import MusicModel
from constants import WINDOW_ICON


class Controller(QWidget):

    ui = None

    def __init__(self, parent=None):
        super().__init__(parent)
        Controller.ui = UiMainWidget()
        ViewApi.ui = Controller.ui
        Controller.ui.setup_ui(self)

        ControllerApi.player = Player()
        ControllerApi.desktop_mini = DesktopMiniLayer()
        ControllerApi.lyric_widget = LyricWidget()
        ControllerApi.notify_widget = NotifyWidget()

        self.network_manger = NetworkManager()
        self.current_playlist_widget = MusicTableWidget()

        self._search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self._switch_mode_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)

        self.network_queue = Queue()

        self._init()

        app_event_loop = asyncio.get_event_loop()
        app_event_loop.call_later(1, self._init_plugins)

    def _init_plugins(self):
        NetEaseMusic.init(self)  # 特例，一般的插件初始化不传参数
        Hotkey.init()

    def _init(self):
        self.setWindowIcon(QIcon(WINDOW_ICON))
        self.setWindowTitle('FeelUOwn')
        self._init_signal_binding()
        self._init_widgets()
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.resize(960, 580)

    def _init_signal_binding(self):
        """初始化部分信号绑定
        :return:
        """
        self.ui.LOGIN_BTN.clicked.connect(self.pop_login)
        self.ui.QUIT_ACTION.triggered.connect(sys.exit)
        self.ui.PLAY_PREVIOUS_SONG_BTN.clicked.connect(ControllerApi.player.play_last)
        self.ui.PLAY_NEXT_SONG_BTN.clicked.connect(ControllerApi.player.play_next)
        self.ui.SONG_PROGRESS_SLIDER.sliderMoved.connect(self.seek)
        self.ui.SHOW_CURRENT_SONGS.clicked.connect(self._show_current_playlist)

        self.ui.SEARCH_BOX.returnPressed.connect(self._search_music)
        self.ui.LOVE_SONG_BTN.clicked.connect(self.on_set_favorite_btn_clicked)
        self.ui.PLAY_MV_BTN.clicked.connect(self.on_play_current_song_mv_clicked)
        self.ui.SHOW_LYRIC_BTN.clicked.connect(ControllerApi.toggle_lyric_widget)

        self.ui.SPREAD_BTN_FOR_MY_LIST.clicked.connect(
            self.ui.MY_LIST_WIDGET.fold_spread_with_animation)
        self.ui.SPREAD_BTN_FOR_COLLECTION.clicked.connect(
            self.ui.COLLECTION_LIST_WIDGET.fold_spread_with_animation)
        self.ui.SPREAD_BTN_FOR_LOCAL.clicked.connect(
            self.ui.LOCAL_LIST_WIDGET.fold_spread_with_animation)

        self.ui.SHOW_DESKTOP_MINI.clicked.connect(self.on_switch_desktop_mini_clicked)

        self.current_playlist_widget.signal_play_music.connect(self.on_play_song_clicked)
        self.current_playlist_widget.signal_remove_music_from_list.connect(self.remove_music_from_list)

        self.ui.PLAY_OR_PAUSE.clicked.connect(self.on_play_or_pause_clicked)

        self.ui.WEBVIEW.loadProgress.connect(self.on_webview_progress)
        self.ui.WEBVIEW.signal_play.connect(self.on_play_song_clicked)
        self.ui.WEBVIEW.signal_play_songs.connect(self.on_play_songs_clicked)
        self.ui.WEBVIEW.signal_play_mv.connect(ControllerApi.play_mv_by_mvid)

        ControllerApi.player.signal_player_media_changed.connect(self._on_player_media_changed)
        ControllerApi.player.stateChanged.connect(self.on_player_state_changed)
        ControllerApi.player.positionChanged.connect(self.on_player_position_changed)
        ControllerApi.player.durationChanged.connect(self.on_player_duration_changed)
        ControllerApi.player.signal_playlist_is_empty.connect(self.on_playlist_empty)
        ControllerApi.player.signal_playback_mode_changed.connect(
            self.ui.STATUS_BAR.playmode_switch_label.on_mode_changed)

        self.network_manger.finished.connect(self._access_network_queue)

        self._search_shortcut.activated.connect(self.set_search_focus)
        self._switch_mode_shortcut.activated.connect(self.on_switch_desktop_mini_clicked)

        ControllerApi.desktop_mini.content.set_song_like_signal.connect(self.on_set_favorite_btn_clicked)
        ControllerApi.desktop_mini.content.play_last_music_signal.connect(ControllerApi.player.play_last)
        ControllerApi.desktop_mini.content.play_next_music_signal.connect(ControllerApi.player.play_next)
        ControllerApi.desktop_mini.close_signal.connect(self.show)

        self.ui.FM_ITEM.signal_text_btn_clicked.connect(self.load_fm)

    def _init_widgets(self):
        self.current_playlist_widget.resize(500, 200)
        self.current_playlist_widget.close()
        self.ui.PROGRESS.setRange(0, 100)

    """这部分写一些工具
    """

    """这部分写一些交互逻辑
    """
    @func_coroutine
    def set_user(self, data):
        avatar_url = data['avatar']
        request = QNetworkRequest(QUrl(avatar_url))
        self.network_manger.get(request)
        self.network_queue.put(self._show_avatar)
        self._show_user_playlist()

    def set_login(self):
        ControllerApi.state['is_login'] = True
        self.ui.LOVE_SONG_BTN.show()
        self.ui.LOGIN_BTN.hide()

    @func_coroutine
    def _show_user_playlist(self):
        while self.ui.MY_LIST_WIDGET.layout().takeAt(0):
            item = self.ui.MY_LIST_WIDGET.layout().takeAt(0)
            del item
        while self.ui.COLLECTION_LIST_WIDGET.layout().takeAt(0):
            item = self.ui.MY_LIST_WIDGET.layout().takeAt(0)
            del item

        playlists = ControllerApi.api.get_user_playlist()
        if not ControllerApi.api.is_response_ok(playlists):
            return

        for playlist in playlists:
            pid = playlist['id']

            w = PlaylistItem(self)
            w.set_playlist_item(playlist)
            w.signal_text_btn_clicked.connect(self.on_playlist_btn_clicked)

            if ControllerApi.api.is_playlist_mine(playlist):
                self.ui.MY_LIST_WIDGET.layout().addWidget(w)
                if pid == ControllerApi.api.favorite_pid:
                    @func_coroutine
                    def load_favorite_playlist(playlist_id):
                        favorite_playlist_detail = ControllerApi.api.get_playlist_detail(playlist_id, cache=False)
                        ControllerApi.state["current_pid"] = playlist_id
                        self.ui.WEBVIEW.load_playlist(favorite_playlist_detail)
                    load_favorite_playlist(pid)
                else:
                    APP_EVENT_LOOP = asyncio.get_event_loop()
                    APP_EVENT_LOOP.call_soon(ControllerApi.api.get_playlist_detail, pid)
            else:
                self.ui.COLLECTION_LIST_WIDGET.layout().addWidget(w)

    def _show_avatar(self, res):
        """界面改版之后再使用
        :param res:
        :return:
        """
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        if ControllerApi.state['is_login']:
            self.ui.LOGIN_BTN.close()
        self.ui.AVATAR_LABEL.show()

        self.ui.AVATAR_LABEL.setPixmap(pixmap.scaled(55, 55, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def _set_music_icon(self, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        self.ui.ALBUM_IMG_LABEL.setPixmap(pixmap.scaled(self.ui.ALBUM_IMG_LABEL.size(),
                                          Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.setWindowIcon(QIcon(pixmap))
        ControllerApi.desktop_mini.content.setPixmap(pixmap)

    def _show_current_playlist(self):
        self.current_playlist_widget.resize(500, 200)
        if self.current_playlist_widget.isVisible():
            self.current_playlist_widget.close()
            return
        width = self.current_playlist_widget.width()
        p_width = self.width()

        geometry = self.geometry()
        p_x, p_y = geometry.x(), geometry.y()

        x = p_x + p_width - width
        y = self.ui.TOP_WIDGET.height() + p_y - 8

        self.current_playlist_widget.setGeometry(x, y, 500, 300)
        self.current_playlist_widget.show()
        self.current_playlist_widget.setFocus(True)

    @func_coroutine
    @pyqtSlot(bool)
    def on_set_favorite_btn_clicked(self, checked=True):
        if not ControllerApi.state["current_mid"]:
            return False
        data = ControllerApi.api.set_music_to_favorite(ControllerApi.state['current_mid'], checked)
        ControllerApi.desktop_mini.content.is_song_like = checked
        if not ControllerApi.api.is_response_ok(data):
            self.ui.LOVE_SONG_BTN.setChecked(not checked)
            ControllerApi.desktop_mini.content.is_song_like = not checked
            return False
        playlist_detail = ControllerApi.api.get_playlist_detail(ControllerApi.api.favorite_pid, cache=False)
        if not ControllerApi.api.is_response_ok(playlist_detail):
            self.ui.STATUS_BAR.showMessage("刷新 -喜欢列表- 失败")
            return False
        if ControllerApi.state['current_pid'] == ControllerApi.api.favorite_pid:
            LOG.info("喜欢列表的歌曲发生变化")
            self.ui.WEBVIEW.load_playlist(playlist_detail)
        return True

    @pyqtSlot(QNetworkReply)
    def _access_network_queue(self, res):
        if self.network_queue.empty():
            LOG.info('Nothing in network queue')
            return
        item = self.network_queue.get_nowait()
        item(res)

    @pyqtSlot(int)
    def seek(self, seconds):
        ControllerApi.player.setPosition(seconds * 1000)

    @pyqtSlot()
    def pop_login(self):
        if ControllerApi.state['is_login'] is False:
            w = LoginDialog(self)
            w.signal_login_sucess.connect(self.on_login_success)
            w.show()

    @classmethod
    @pyqtSlot()
    def on_play_or_pause_clicked(cls):
        if ControllerApi.player.mediaStatus() == QMediaPlayer.NoMedia or \
                ControllerApi.player.mediaStatus() == QMediaPlayer.UnknownMediaStatus:
            cls.ui.PLAY_OR_PAUSE.setChecked(True)     # 暂停状态
            return
        ControllerApi.player.play_or_pause()

    @pyqtSlot(int)
    def on_player_position_changed(self, ms):
        time_text = QTime(0, (ms / 60000) % 60, (ms / 1000) % 60)
        self.ui.SONG_COUNTDOWN_LABEL.setText(time_text.toString("mm:ss"))
        self.ui.SONG_PROGRESS_SLIDER.setValue(ms / 1000)
        ControllerApi.desktop_mini.content.set_value(ms / 1000)

        ControllerApi.lyric_widget.show_lyric_while_visible(ms)

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
        playlist_detail = ControllerApi.api.get_playlist_detail(pid)
        if not ControllerApi.api.is_response_ok(playlist_detail):
            return
        self.ui.WEBVIEW.load_playlist(playlist_detail)
        # TODO: change current_pid when webview changed
        ControllerApi.state['current_pid'] = pid

    @pyqtSlot(int)
    def on_webview_progress(self, percent):
        self.ui.PROGRESS.setValue(percent)

    @func_coroutine
    @pyqtSlot(int)
    def on_play_song_clicked(self, mid=None):
        self.exit_fm()
        songs = ControllerApi.api.get_song_detail(mid)
        if not ControllerApi.api.is_response_ok(songs):
            return

        if len(songs) == 0:
            self.ui.STATUS_BAR.showMessage(u'这首音乐在地震中消失了', 4000)
            return
        ControllerApi.player.play(songs[0])

    @func_coroutine
    def on_play_current_song_mv_clicked(self, clicked=True):
        mid = ControllerApi.state['current_mid']
        data = ControllerApi.api.get_song_detail(mid)
        if not ControllerApi.api.is_response_ok(data):
            return
        music_model = data[0]

        mvid = music_model['mvid']
        ControllerApi.play_mv_by_mvid(int(mvid))

    def on_switch_desktop_mini_clicked(self):
        if ControllerApi.desktop_mini.isVisible():
            self.show()
        else:
            if platform.system().lower() == "darwin":
                self.showMinimized()
            else:
                self.hide()
        ControllerApi.toggle_desktop_mini()

    @pyqtSlot(int)
    def on_play_songs_clicked(self, songs):
        self.exit_fm()
        if len(songs) == 0:
            self.ui.STATUS_BAR.showMessage(u'该列表没有歌曲', 2000)
            return
        self.current_playlist_widget.set_songs(songs)
        ControllerApi.player.set_music_list(songs)

    @pyqtSlot(dict)
    def _on_player_media_changed(self, music_model):
        artists = music_model['artists']
        artists_name = ''
        for artist in artists:
            artists_name += artist['name']
        title = music_model['name'] + ' - ' + artists_name
        ControllerApi.desktop_mini.content.set_song_name(music_model['name'])
        ControllerApi.desktop_mini.content.set_song_singer(artists_name)
        self.setWindowTitle(title)
        
        metrics = QFontMetrics(self.ui.TOP_WIDGET.font())
        title = metrics.elidedText(title, Qt.ElideRight, 300 - 40)
        self.ui.SONG_NAME_LABEL.setText(title)
        ControllerApi.lyric_widget.reset_lyric()

        self.ui.SONG_COUNTDOWN_LABEL.setText('00:00')
        self.ui.SONG_PROGRESS_SLIDER.setRange(0, ControllerApi.player.duration() / 1000)
        ControllerApi.desktop_mini.content.set_duration(ControllerApi.player.duration() / 1000)

        self.network_manger.get(QNetworkRequest(QUrl(music_model['album']['picUrl'] + "?param=200y200")))
        self.network_queue.put(self._set_music_icon)    # 更换任务栏图标

        self.current_playlist_widget.add_item_from_model(music_model)
        self.current_playlist_widget.focus_cell_by_mid(music_model['id'])

        ControllerApi.state['current_mid'] = music_model['id']

        if MusicModel.mv_available(music_model):
            self.ui.PLAY_MV_BTN.show()
        else:
            self.ui.PLAY_MV_BTN.close()
        if ControllerApi.state['is_login']:
            if ControllerApi.api.is_favorite_music(music_model['id']):
                self.ui.LOVE_SONG_BTN.setChecked(True)
                ControllerApi.desktop_mini.content.is_song_like = True
            else:
                self.ui.LOVE_SONG_BTN.setChecked(False)
                ControllerApi.desktop_mini.content.is_song_like = False

    @pyqtSlot()
    def load_fm(self):
        """播放FM

        1. webkit加载FM播放页面，可以有点动画和设计
        2. 由于播放FM，要时常向服务器请求歌曲，所以逻辑跟正常播放时有点不一样
        """
        ControllerApi.state['fm'] = True
        ControllerApi.player.change_player_mode()
        ControllerApi.notify_widget.show_message("Info", "进入FM播放模式")
        FmMode.load(self)
        ControllerApi.player.signal_playlist_finished.connect(FmMode.on_next_music_required)

    @pyqtSlot()
    def exit_fm(self):
        """如果从webview播放一首歌，就退出fm模式，暂时使用这个逻辑

        TODO:
        """
        if ControllerApi.state['fm']:
            ControllerApi.player.change_player_mode()
            ControllerApi.notify_widget.show_message("Info", "退出FM播放模式")
            FmMode.exit()
            ControllerApi.state['fm'] = False

    @pyqtSlot(int)
    def on_player_duration_changed(self, duration):
        self.ui.SONG_PROGRESS_SLIDER.setRange(0, ControllerApi.player.duration() / 1000)
        ControllerApi.desktop_mini.content.set_duration(ControllerApi.player.duration() / 1000)

    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.ui.PLAY_OR_PAUSE.setChecked(False)
        else:
            self.ui.PLAY_OR_PAUSE.setChecked(True)

    @pyqtSlot(int)
    def remove_music_from_list(self, mid):
        ControllerApi.player.remove_music(mid)

    @pyqtSlot()
    def on_playlist_empty(self):
        self.ui.SONG_NAME_LABEL.setText(u'当前没有歌曲播放')
        self.ui.SONG_COUNTDOWN_LABEL.setText('00:00')
        self.ui.PLAY_OR_PAUSE.setChecked(True)

    @pyqtSlot()
    def set_search_focus(self):
        self.ui.SEARCH_BOX.setFocus()

    @func_coroutine
    @pyqtSlot()
    def _search_music(self):
        text = self.ui.SEARCH_BOX.text()
        if text != '':
            self.ui.STATUS_BAR.showMessage(u'正在搜索: ' + text)
            songs = ControllerApi.api.search(text)
            if not ControllerApi.api.is_response_ok(songs):
                return
            PlaylistItem.de_active_all()
            self.ui.WEBVIEW.load_search_result(songs)
            ControllerApi.state['current_pid'] = 0
            length = len(songs)
            if length != 0:
                self.ui.STATUS_BAR.showMessage(u'搜索到 ' + str(length) + u' 首 ' + text + u' 相关歌曲', 5000)
                return
            else:
                self.ui.STATUS_BAR.showMessage(u'很抱歉，没有找到相关歌曲', 5000)
                return

    @pyqtSlot(int)
    def on_web_load_progress(self, progress):
        QApplication.processEvents()
        self.ui.PROGRESS.setValue(progress)

    def paintEvent(self, event: QPaintEvent):
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

    def closeEvent(self, event):
        self.close()


class FmMode():
    """fm mode 一些说明
    
    当切换到fm播放模式的时候，每向服务器请求一次，服务器会返回几首歌曲
    所以当这几首歌曲播放结束的时候，我们要向服务器请求下几首歌
    """
    _api = None
    _player = None
    _notify = None
    _controller = None
    _songs = []     # brief music model

    @classmethod
    def load(cls, controller):

        cls._notify = NotifyWidget()

        cls._controller = controller

        cls._api = ControllerApi.api
        cls._player = Player()
        cls._player.stop()

        cls.reset_song_list()

    @classmethod
    def reset_song_list(cls):
        cls._player.clear_playlist()
        if len(cls._songs) > 0:
            song = cls._songs.pop()
            mid = song['id']
            music_models = cls._api.get_song_detail(mid)
            if not ControllerApi.api.is_response_ok(music_models):
                cls._controller.exit_fm()
                return
            cls._player.set_music_list([music_models[0]])
        else:
            cls._songs = cls._api.get_radio_songs()
            if not ControllerApi.api.is_response_ok(cls._songs):
                cls._player.stop()
                cls._notify.show_message("Error", "网络异常，请检查网络连接")
                cls._controller.exit_fm()
            else:
                cls.reset_song_list()

    @classmethod
    @pyqtSlot()
    def on_next_music_required(cls):
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        cls._player = None
        cls._api = None
        cls._notify = None
        cls._controller = None
