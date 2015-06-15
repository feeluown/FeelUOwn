# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys, time
from queue import Queue

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtMultimedia import *

from widgets.login_dialog import LoginDialog
from widgets.playlist_widget import PlaylistWidget, PlaylistItem

from views import UiMainWidget

from base.models import DataModel
from base.player import Player
from base.network_manger import NetworkManager
from base.logger import LOG

from api import Api
from setting import WINDOW_ICON


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        # QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()    # 那些widget对象都通过self.ui.*.*来访问，感觉也不是很好
        self.ui.setup_ui(self)

        self.player = Player()
        self.status = self.ui.status
        self.webview = self.ui.right_widget.webview     # 常用的对象复制一下，方便使用
        self.progress = self.ui.top_widget.progress_info
        self.network_manger = NetworkManager()

        self.play_or_pause_btn = self.ui.top_widget.play_pause_btn

        self.api = Api()
        self.network_queue = Queue()

        self.init()

        self.state = {'is_login': False}

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def init(self):
        # self.setWindowIcon(QIcon(WINDOW_ICON))
        self.init_signal_binding()
        self.init_player()
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.resize(960, 580)

    def init_player(self):
        pass

    def init_signal_binding(self):
        """初始化部分信号绑定
        :return:
        """
        self.ui.top_widget.login_btn.clicked.connect(self.pop_login)
        self.ui.top_widget.last_music_btn.clicked.connect(self.last_music)
        self.ui.top_widget.next_music_btn.clicked.connect(self.next_music)
        self.ui.top_widget.slider_play.sliderMoved.connect(self.seek)
        self.play_or_pause_btn.clicked.connect(self.play_or_pause)

        self.webview.loadProgress.connect(self.on_webview_progress)
        self.webview.signal_play.connect(self.play)

        self.player.signal_player_media_changed.connect(self.on_player_media_changed)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)

        self.network_manger.finished.connect(self.access_network_queue)

    """这部分写一些交互逻辑
    """
    def show_user_playlist(self):
        playlists = self.api.get_user_playlist()
        for playlist in playlists:
            w = PlaylistItem(self)
            w.set_playlist_item(playlist)

            # 感觉这句话增加了耦合度, 暂时没找到好的解决办法
            w.signal_text_btn_clicked.connect(self.on_playlist_btn_clicked)

            if self.api.is_playlist_mine(playlist):
                self.ui.left_widget.central_widget.create_list_widget.layout.addWidget(w)
            else:
                self.ui.left_widget.central_widget.collection_list_widget.layout.addWidget(w)

    def show_avatar(self, res):
        """界面改版之后再使用
        :param res:
        :return:
        """
        return

    def set_music_icon(self, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        self.ui.top_widget.img_label.setPixmap(pixmap)
        self.setWindowIcon(QIcon(pixmap))

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
        if self.player.mediaStatus() == QMediaPlayer.NoMedia:
            self.play_or_pause_btn.setChecked(True)     # 暂停状态
            return
        self.player.play_or_pause()

    @pyqtSlot(int)
    def on_player_position_changed(self, ms):
        time_text = QTime(0, (ms / 60000) % 60, (ms / 1000) % 60)
        self.ui.top_widget.time_lcd.setText(time_text.toString())
        self.ui.top_widget.slider_play.setValue(ms / 1000)

    @pyqtSlot(dict)
    def on_login_success(self, data):
        """
        登陆成功
        :param data:
        :return:
        """
        self.state['is_login'] = True
        avatar_url = data['avatar']
        request = QNetworkRequest(QUrl(avatar_url))
        self.network_manger.get(request)

        self.network_queue.put(self.show_avatar)

        self.show_user_playlist()

    @pyqtSlot(int)
    def on_playlist_btn_clicked(self, pid):
        self.progress.setValue(0)   # 恢复0的状态

        playlist_detail = self.api.get_playlist_detail(pid)  # 这个操作特别耗时

        self.progress.setValue(50)  # 暂时设为50，告诉用户它的操作成功了一半,但是之后的操作会再次归零
        self.webview.load_playlist(playlist_detail)

    @pyqtSlot(int)
    def on_webview_progress(self, percent):
        self.progress.setValue(percent)

    @pyqtSlot(int)
    def play(self, pid=None):
        songs = self.api.get_song_detail(pid)
        if len(songs) == 0:
            self.status.showMessage(u'这首音乐在地震中消失了')
            return
        self.player.play(songs[0])

    @pyqtSlot(dict)
    def on_player_media_changed(self, music_model):
        artists = music_model['artists']
        artists_name = ''
        for artist in artists:
            artists_name += artist['name']
        title = music_model['name'] + ' - ' + artists_name
        self.ui.top_widget.text_label.setText(title)
        self.ui.top_widget.time_lcd.setText('00:00')
        self.ui.top_widget.slider_play.setRange(0, self.player.duration() / 1000)

        self.network_manger.get(QNetworkRequest(QUrl(music_model['album']['picUrl'])))
        self.network_queue.put(self.set_music_icon)    # 更换任务栏图标

    @pyqtSlot(int)
    def on_player_duration_changed(self, duration):
        self.ui.top_widget.slider_play.setRange(0, self.player.duration() / 1000)

    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_or_pause_btn.setChecked(False)
        else:
            self.play_or_pause_btn.setChecked(True)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
