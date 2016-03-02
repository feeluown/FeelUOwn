# -*- coding: utf-8 -*-

import asyncio

from PyQt5.QtCore import pyqtSlot, QTime, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWidgets import QApplication

from feeluown.logger import LOG
from feeluown.models import MusicModel
from feeluown.utils import measure_time
from feeluown.widgets.playlist_widget import PlaylistItem


class ViewOp(object):
    ui = None

    @classmethod
    def set_login_label_avatar(cls, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        if cls.controller.state['is_login']:
            cls.ui.LOGIN_BTN.close()
        cls.ui.AVATAR_LABEL.show()
        width = cls.ui.AVATAR_LABEL.size().width()
        cls.ui.AVATAR_LABEL.setPixmap(pixmap.scaled(width, width, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    @classmethod
    def set_music_cover_img(cls, res):
        img = QImage()
        img.loadFromData(res.readAll())
        pixmap = QPixmap(img)
        cls.ui.ALBUM_IMG_LABEL.setPixmap(pixmap.scaled(cls.ui.ALBUM_IMG_LABEL.size(),
                                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        QApplication.setWindowIcon(QIcon(pixmap))
        cls.controller.desktop_mini.content.setPixmap(pixmap)

    @classmethod
    def new_playlist(cls):
        playlist = cls.controller.api.new_playlist('default')
        if playlist is None:
            cls.controller.notify_widget.show_message('◕◠◔', '新建歌单失败')
            return False
        w = PlaylistItem()
        w.set_playlist_item(playlist)
        w.signal_text_btn_clicked.connect(cls.on_playlist_btn_clicked)
        ViewOp.ui.MY_LIST_WIDGET.layout().addWidget(w)
        w.edit_mode()
        return True

    @classmethod
    @pyqtSlot()
    def on_play_or_pause_clicked(cls):
        if cls.controller.player.mediaStatus() == QMediaPlayer.NoMedia or \
                cls.controller.player.mediaStatus() == QMediaPlayer.UnknownMediaStatus:
            ViewOp.ui.PLAY_OR_PAUSE.setChecked(True)     # 暂停状态
            return
        cls.controller.player.play_or_pause()

    @classmethod
    @pyqtSlot(int)
    def on_player_position_changed(cls, ms):
        time_text = QTime(0, (ms / 60000) % 60, (ms / 1000) % 60)
        cls.ui.SONG_COUNTDOWN_LABEL.setText(time_text.toString("mm:ss"))
        cls.ui.SONG_PROGRESS_SLIDER.setValue(ms / 1000)
        cls.controller.desktop_mini.content.set_value(ms / 1000)
        cls.controller.lyric_widget.show_lyric_while_visible(ms)

    @classmethod
    @pyqtSlot(int)
    def on_player_duration_changed(cls, duration):
        cls.ui.SONG_PROGRESS_SLIDER.setRange(0, duration / 1000)
        cls.controller.desktop_mini.content.set_duration(cls.controller.player.duration() / 1000)

    @classmethod
    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(cls, state):
        if state == QMediaPlayer.PlayingState:
            cls.ui.PLAY_OR_PAUSE.setChecked(False)
        else:
            cls.ui.PLAY_OR_PAUSE.setChecked(True)

    @classmethod
    @pyqtSlot(bool)
    def on_play_current_song_mv_clicked(cls, clicked=True):
        mid = cls.controller.state['current_mid']
        song = cls.controller.api.get_song_detail(mid)
        print('song:', type(song))
        if not cls.controller.api.is_response_ok(song):
            return
        mvid = song['mvid']
        cls.controller.play_mv_by_mvid(int(mvid))

    @classmethod
    @pyqtSlot(bool)
    def on_set_favorite_btn_clicked(cls, checked=True):
        if not cls.controller.state["current_mid"]:
            return False
        data = cls.controller.api.set_music_to_favorite(cls.controller.state['current_mid'], checked)
        cls.controller.desktop_mini.content.is_song_like = checked
        if not cls.controller.api.is_response_ok(data):
            ViewOp.ui.LOVE_SONG_BTN.setChecked(not checked)
            cls.controller.desktop_mini.content.is_song_like = not checked
            return False
        playlist_detail = cls.controller.api.get_playlist_detail(cls.controller.api.favorite_pid, cache=False)
        if not cls.controller.api.is_response_ok(playlist_detail):
            ViewOp.ui.STATUS_BAR.showMessage("刷新 -喜欢列表- 失败")
            return False
        if cls.controller.state['current_pid'] == cls.controller.api.favorite_pid:
            LOG.info("喜欢列表的歌曲发生变化")
            # ViewOp.ui.WEBVIEW.load_playlist(playlist_detail)
        return True

    @classmethod
    @pyqtSlot(dict)
    def on_player_media_changed(cls, music_model):
        artists = music_model['artists']
        artists_name = ''
        for artist in artists:
            artists_name += artist['name']
        title = music_model['name'] + ' - ' + artists_name
        cls.controller.desktop_mini.content.set_song_name(music_model['name'])
        cls.controller.desktop_mini.content.set_song_singer(artists_name)

        metrics = QFontMetrics(ViewOp.ui.TOP_WIDGET.font())
        title = metrics.elidedText(title, Qt.ElideRight, 300 - 40)
        ViewOp.ui.SONG_NAME_LABEL.setText(title)
        cls.controller.lyric_widget.reset_lyric()

        ViewOp.ui.SONG_COUNTDOWN_LABEL.setText('00:00')
        ViewOp.ui.SONG_PROGRESS_SLIDER.setRange(0, cls.controller.player.duration() / 1000)
        cls.controller.desktop_mini.content.set_duration(cls.controller.player.duration() / 1000)

        cls.controller.network_manager.get(QNetworkRequest(QUrl(music_model['album']['picUrl'] + "?param=200y200")))
        cls.controller.network_manager.network_queue.put(ViewOp.set_music_cover_img)

        cls.controller.current_playlist_widget.add_item_from_model(music_model)
        cls.controller.current_playlist_widget.focus_cell_by_mid(music_model['id'])

        cls.controller.state['current_mid'] = music_model['id']

        if MusicModel.mv_available(music_model):
            ViewOp.ui.PLAY_MV_BTN.show()
        else:
            ViewOp.ui.PLAY_MV_BTN.close()
        if cls.controller.state['is_login']:
            if cls.controller.api.is_favorite_music(music_model['id']):
                ViewOp.ui.LOVE_SONG_BTN.setChecked(True)
                cls.controller.desktop_mini.content.is_song_like = True
            else:
                ViewOp.ui.LOVE_SONG_BTN.setChecked(False)
                cls.controller.desktop_mini.content.is_song_like = False

    @classmethod
    @measure_time
    def load_user_infos(cls, data):
        avatar_url = data['avatar']
        request = QNetworkRequest(QUrl(avatar_url))
        cls.controller.network_manager.get(request)
        cls.controller.network_manager.network_queue.put(ViewOp.set_login_label_avatar)

        ViewOp.ui.MY_LIST_WIDGET.empty_layout()
        ViewOp.ui.COLLECTION_LIST_WIDGET.empty_layout()

        playlists = cls.controller.api.get_user_playlist()
        if not cls.controller.api.is_response_ok(playlists):
            return

        playlist_num = len(playlists)

        for playlist in playlists:
            pid = playlist['id']

            w = PlaylistItem()
            w.set_playlist_item(playlist)
            w.signal_text_btn_clicked.connect(cls.on_playlist_btn_clicked)

            if cls.controller.api.is_playlist_mine(playlist):
                ViewOp.ui.MY_LIST_WIDGET.layout().addWidget(w)
                if pid == cls.controller.api.favorite_pid:
                    favorite_playlist_detail = cls.controller.api.get_playlist_detail(pid)
                    cls.controller.state["current_pid"] = pid
                    ViewOp.ui.WEBVIEW.load_playlist(favorite_playlist_detail)
                else:
                    if playlist_num <= 50:
                        app_event_loop = asyncio.get_event_loop()
                        app_event_loop.call_soon(cls.controller.api.get_playlist_detail, pid)
            else:
                ViewOp.ui.COLLECTION_LIST_WIDGET.layout().addWidget(w)
        LOG.info('load user infos finished')

    @classmethod
    @pyqtSlot(int)
    def on_playlist_btn_clicked(cls, pid):
        playlist_detail = cls.controller.api.get_playlist_detail(
            pid, cache=False)
        if not cls.controller.api.is_response_ok(playlist_detail):
            return
        cls.ui.WEBVIEW.load_playlist(playlist_detail)
        # TODO: change current_pid when webview changed
        cls.controller.state['current_pid'] = pid

    @classmethod
    @pyqtSlot()
    def on_recommend_item_clicked(cls):
        songs = cls.controller.api.get_recommend_songs()
        if not cls.controller.api.is_response_ok(songs):
            return
        # cls.ui.WEBVIEW.load_recommend_songs(songs)
        cls.controller.state['current_pid'] = 0
