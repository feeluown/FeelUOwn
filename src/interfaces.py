# -*- coding:utf8 -*-

import platform
import subprocess
import asyncio

from PyQt5.QtCore import pyqtSlot, QTime, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWidgets import QApplication

from base.utils import func_coroutine
from base.logger import LOG
from base.models import MusicModel

from widgets.playlist_widget import PlaylistItem


class ControllerApi(object):
    """暴露给plugin或者其他外部模块的接口和数据
    """
    notify_widget = None
    lyric_widget = None
    desktop_mini = None
    current_playlist_widget = None
    player = None
    network_manager = None
    api = None

    state = {"is_login": False,
             "current_mid": 0,
             "current_pid": 0,
             "platform": "",
             "fm": False}

    @classmethod
    def set_login(cls):
        cls.state['is_login'] = True
        ViewOp.ui.LOVE_SONG_BTN.show()
        ViewOp.ui.LOGIN_BTN.hide()

    @classmethod
    def play_mv_by_mvid(cls, mvid):
        mv_model = ControllerApi.api.get_mv_detail(mvid)
        if not ControllerApi.api.is_response_ok(mv_model):
            return

        url_high = mv_model['url_high']
        clipboard = QApplication.clipboard()
        clipboard.setText(url_high)

        if platform.system() == "Linux":
            ControllerApi.player.pause()
            ControllerApi.notify_widget.show_message("通知", "正在尝试调用VLC视频播放器播放MV")
            subprocess.Popen(['vlc', url_high, '--play-and-exit', '-f'])
        elif platform.system().lower() == 'Darwin'.lower():
            ControllerApi.player.pause()
            ViewOp.ui.STATUS_BAR.showMessage(u"准备调用 QuickTime Player 播放mv", 4000)
            subprocess.Popen(['open', '-a', 'QuickTime Player', url_high])
        else:
            ViewOp.ui.STATUS_BAR.showMessage(u"您的系统不是Linux。程序已经将视频的播放地址复制到剪切板，你可以使用你喜欢的播放器播放视频", 5000)

    @classmethod
    def toggle_lyric_widget(cls):
        if ControllerApi.lyric_widget.isVisible():
            ControllerApi.lyric_widget.close()
        else:
            ControllerApi.lyric_widget.show()

    @classmethod
    def toggle_desktop_mini(cls):
        if ControllerApi.desktop_mini.isVisible():
            ControllerApi.desktop_mini.close()
        else:
            ControllerApi.desktop_mini.show()
            ControllerApi.notify_widget.show_message("Tips", "按ESC可以退出mini模式哦 ~")

    @classmethod
    @pyqtSlot(int)
    def seek(cls, seconds):
        cls.player.setPosition(seconds * 1000)


class ViewOp(object):
    ui = None

    @classmethod
    def set_login_label_avatar(cls, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        if ControllerApi.state['is_login']:
            ViewOp.ui.LOGIN_BTN.close()
        cls.ui.AVATAR_LABEL.show()
        width = cls.ui.AVATAR_LABEL.size().width()
        cls.ui.AVATAR_LABEL.setPixmap(pixmap.scaled(width, width, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    @classmethod
    def set_music_icon(cls, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        cls.ui.ALBUM_IMG_LABEL.setPixmap(pixmap.scaled(cls.ui.ALBUM_IMG_LABEL.size(),
                                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        QApplication.setWindowIcon(QIcon(pixmap))
        ControllerApi.desktop_mini.content.setPixmap(pixmap)

    @staticmethod
    @pyqtSlot()
    def on_play_or_pause_clicked():
        if ControllerApi.player.mediaStatus() == QMediaPlayer.NoMedia or \
                ControllerApi.player.mediaStatus() == QMediaPlayer.UnknownMediaStatus:
            ViewOp.ui.PLAY_OR_PAUSE.setChecked(True)     # 暂停状态
            return
        ControllerApi.player.play_or_pause()

    @classmethod
    @pyqtSlot(int)
    def on_player_position_changed(cls, ms):
        time_text = QTime(0, (ms / 60000) % 60, (ms / 1000) % 60)
        cls.ui.SONG_COUNTDOWN_LABEL.setText(time_text.toString("mm:ss"))
        cls.ui.SONG_PROGRESS_SLIDER.setValue(ms / 1000)
        ControllerApi.desktop_mini.content.set_value(ms / 1000)
        ControllerApi.lyric_widget.show_lyric_while_visible(ms)

    @classmethod
    @pyqtSlot(int)
    def on_player_duration_changed(cls, duration):
        cls.ui.SONG_PROGRESS_SLIDER.setRange(0, duration / 1000)
        ControllerApi.desktop_mini.content.set_duration(ControllerApi.player.duration() / 1000)

    @classmethod
    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(cls, state):
        if state == QMediaPlayer.PlayingState:
            cls.ui.PLAY_OR_PAUSE.setChecked(False)
        else:
            cls.ui.PLAY_OR_PAUSE.setChecked(True)

    @func_coroutine
    @pyqtSlot(bool)
    def on_play_current_song_mv_clicked(self, clicked=True):
        mid = ControllerApi.state['current_mid']
        data = ControllerApi.api.get_song_detail(mid)
        if not ControllerApi.api.is_response_ok(data):
            return
        music_model = data[0]

        mvid = music_model['mvid']
        ControllerApi.play_mv_by_mvid(int(mvid))

    @func_coroutine
    @pyqtSlot(bool)
    def on_set_favorite_btn_clicked(self, checked=True):
        if not ControllerApi.state["current_mid"]:
            return False
        data = ControllerApi.api.set_music_to_favorite(ControllerApi.state['current_mid'], checked)
        ControllerApi.desktop_mini.content.is_song_like = checked
        if not ControllerApi.api.is_response_ok(data):
            ViewOp.ui.LOVE_SONG_BTN.setChecked(not checked)
            ControllerApi.desktop_mini.content.is_song_like = not checked
            return False
        playlist_detail = ControllerApi.api.get_playlist_detail(ControllerApi.api.favorite_pid, cache=False)
        if not ControllerApi.api.is_response_ok(playlist_detail):
            ViewOp.ui.STATUS_BAR.showMessage("刷新 -喜欢列表- 失败")
            return False
        if ControllerApi.state['current_pid'] == ControllerApi.api.favorite_pid:
            LOG.info("喜欢列表的歌曲发生变化")
            ViewOp.ui.WEBVIEW.load_playlist(playlist_detail)
        return True

    @classmethod
    @pyqtSlot(dict)
    def on_player_media_changed(cls, music_model):
        print (music_model)
        artists = music_model['artists']
        artists_name = ''
        for artist in artists:
            artists_name += artist['name']
        title = music_model['name'] + ' - ' + artists_name
        ControllerApi.desktop_mini.content.set_song_name(music_model['name'])
        ControllerApi.desktop_mini.content.set_song_singer(artists_name)

        metrics = QFontMetrics(ViewOp.ui.TOP_WIDGET.font())
        title = metrics.elidedText(title, Qt.ElideRight, 300 - 40)
        ViewOp.ui.SONG_NAME_LABEL.setText(title)
        ControllerApi.lyric_widget.reset_lyric()

        ViewOp.ui.SONG_COUNTDOWN_LABEL.setText('00:00')
        ViewOp.ui.SONG_PROGRESS_SLIDER.setRange(0, ControllerApi.player.duration() / 1000)
        ControllerApi.desktop_mini.content.set_duration(ControllerApi.player.duration() / 1000)

        ControllerApi.network_manager.get(QNetworkRequest(QUrl(music_model['album']['picUrl'] + "?param=200y200")))
        ControllerApi.network_manager.network_queue.put(ViewOp.set_music_icon)

        ControllerApi.current_playlist_widget.add_item_from_model(music_model)
        ControllerApi.current_playlist_widget.focus_cell_by_mid(music_model['id'])

        ControllerApi.state['current_mid'] = music_model['id']

        if MusicModel.mv_available(music_model):
            ViewOp.ui.PLAY_MV_BTN.show()
        else:
            ViewOp.ui.PLAY_MV_BTN.close()
        if ControllerApi.state['is_login']:
            if ControllerApi.api.is_favorite_music(music_model['id']):
                ViewOp.ui.LOVE_SONG_BTN.setChecked(True)
                ControllerApi.desktop_mini.content.is_song_like = True
            else:
                ViewOp.ui.LOVE_SONG_BTN.setChecked(False)
                ControllerApi.desktop_mini.content.is_song_like = False

    @classmethod
    @func_coroutine
    def load_user_infos(cls, data):
        avatar_url = data['avatar']
        request = QNetworkRequest(QUrl(avatar_url))
        ControllerApi.network_manager.get(request)
        ControllerApi.network_manager.network_queue.put(ViewOp.set_login_label_avatar)

        ViewOp.ui.MY_LIST_WIDGET.empty_layout()
        ViewOp.ui.COLLECTION_LIST_WIDGET.empty_layout()

        playlists = ControllerApi.api.get_user_playlist()
        if not ControllerApi.api.is_response_ok(playlists):
            return

        for playlist in playlists:
            pid = playlist['id']

            w = PlaylistItem()
            w.set_playlist_item(playlist)
            w.signal_text_btn_clicked.connect(cls.on_playlist_btn_clicked)

            if ControllerApi.api.is_playlist_mine(playlist):
                ViewOp.ui.MY_LIST_WIDGET.layout().addWidget(w)
                if pid == ControllerApi.api.favorite_pid:
                    @func_coroutine
                    def load_favorite_playlist(playlist_id):
                        favorite_playlist_detail = ControllerApi.api.get_playlist_detail(playlist_id, cache=False)
                        ControllerApi.state["current_pid"] = playlist_id
                        ViewOp.ui.WEBVIEW.load_playlist(favorite_playlist_detail)
                    load_favorite_playlist(pid)
                else:
                    app_event_loop = asyncio.get_event_loop()
                    app_event_loop.call_soon(ControllerApi.api.get_playlist_detail, pid)
            else:
                ViewOp.ui.COLLECTION_LIST_WIDGET.layout().addWidget(w)

    @classmethod
    @func_coroutine
    @pyqtSlot(int)
    def on_playlist_btn_clicked(cls, pid):
        playlist_detail = ControllerApi.api.get_playlist_detail(pid)
        if not ControllerApi.api.is_response_ok(playlist_detail):
            return
        cls.ui.WEBVIEW.load_playlist(playlist_detail)
        # TODO: change current_pid when webview changed
        ControllerApi.state['current_pid'] = pid
