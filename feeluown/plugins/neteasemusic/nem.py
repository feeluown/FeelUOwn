import asyncio
import json
import logging
import os
from functools import partial

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QKeySequence
from PyQt5.QtMultimedia import QMediaPlayer

from .api import api
from .consts import USER_PW_FILE
from .downloader import Downloader
from .fm_player_mode import FM_mode
from .simi_player_mode import Simi_mode
from .model import (NUserModel, NSongModel, NArtistModel,
                    NAlbumModel, NPlaylistModel)
from .ui import Ui, SongsTable, PlaylistItem

logger = logging.getLogger(__name__)


class Nem(QObject):

    def __init__(self, app):
        super().__init__(parent=app)
        self._app = app
        api.set_http(self._app.request)

        self.ui = Ui(self._app)
        self.downloader = Downloader(self._app, self)

        self.user = None
        self.download_queue = []

        self.registe_hotkey()
        self.init_signal_binding()

    def init_signal_binding(self):
        self.downloader.download_progress_signal.connect(
            self._app.show_request_progress)
        self.ui.login_btn.clicked.connect(self.ready_to_login)
        self.ui.login_dialog.ok_btn.clicked.connect(self.login)
        self.ui.songs_table_container.table_control.play_all_btn.clicked\
            .connect(self.play_all)
        self.ui.songs_table_container.table_control.search_box.textChanged\
            .connect(self.search_table)
        self.ui.songs_table_container.table_control.search_box.returnPressed\
            .connect(self.search_net)

        self.ui.fm_item.clicked.connect(self.enter_fm_mode)
        self.ui.recommend_item.clicked.connect(self.show_recommend_songs)
        self.ui.simi_item.clicked.connect(self.enter_simi_mode)

        self._app.player.stateChanged.connect(
            self.on_player_state_changed)
        self._app.player.signal_player_media_changed.connect(
            self.on_player_media_changed)

    def enter_fm_mode(self):
        mode = FM_mode(self._app)
        self._app.player_mode_manager.enter_mode(mode)

    def enter_simi_mode(self):
        mode = Simi_mode(self._app)
        self._app.player_mode_manager.enter_mode(mode)

    def registe_hotkey(self):
        self._app.hotkey_manager.registe(
            QKeySequence('Ctrl+F'),
            self.ui.songs_table_container.table_control.search_box.setFocus)

    def show_recommend_songs(self):
        songs = NUserModel.get_recommend_songs()
        songs_table = SongsTable(self._app)
        self.load_songs(songs, songs_table)

    def load_user_pw(self):
        if not os.path.exists(USER_PW_FILE):
            return
        with open(USER_PW_FILE, 'r') as f:
            d = json.load(f)
            data = d[d['default']]
        self.ui.login_dialog.username_input.setText(data['username'])
        self.ui.login_dialog.pw_input.setText(data['password'])
        self.ui.login_dialog.is_encrypted = True

        logger.info('load username and password from %s' % USER_PW_FILE)

    def save_user_pw(self, data):
        with open(USER_PW_FILE, 'w+') as f:
            if f.read() == '':
                d = dict()
            else:
                d = json.load(f)
            d['default'] = data['username']
            d[d['default']] = data
            json.dump(d, f, indent=4)

        logger.info('save username and password to %s' % USER_PW_FILE)

    def ready_to_login(self):
        # Only refresh playlists when a user already exists
        if self.user:
            self.load_playlists()

        else:
            model = NUserModel.load()
            if model is None:
                self.ui.login_dialog.show()
                self.load_user_pw()
            else:
                logger.info('load last user.')
                self.user = model
                NUserModel.set_current_user(model)
                self._on_login_in()

    def login(self):
        login_dialog = self.ui.login_dialog
        if login_dialog.captcha_needed:
            captcha = str(login_dialog.captcha_input.text())
            captcha_id = login_dialog.captcha_id
            data = NUserModel.check_captcha(captcha_id, captcha)
            if data['code'] == 200:
                login_dialog.captcha_input.hide()
                login_dialog.captcha_label.hide()
            else:
                login_dialog.captcha_verify(data)

        user_data = login_dialog.data
        self.ui.login_dialog.show_hint('正在登录...')
        data = NUserModel.check(user_data['username'], user_data['password'])
        message = data['message']
        self.ui.login_dialog.show_hint(message)
        if data['code'] == 200:
            # login in
            self.save_user_pw(user_data)
            self.user = NUserModel.create(data)
            self._on_login_in()
        elif data['code'] == 415:
            login_dialog.captcha_verify(data)

    def _on_login_in(self):
        logger.info('login in... set user infos.')

        self.ui.on_login_in()

        app_event_loop = asyncio.get_event_loop()
        app_event_loop.run_in_executor(
            None,
            partial(self.ui.login_btn.set_avatar, self.user.img))
        self.user.save()
        self.load_playlists()

    def load_playlists(self):
        self._app.message('正在加载网易云音乐歌单')
        playlist_widget = self._app.ui.central_panel.left_panel.playlists_panel
        for playlist in self.user.playlists:
            item = PlaylistItem(self._app, playlist)
            if item.existed:
                continue
            item.load_playlist_signal.connect(self.load_playlist)
            playlist_widget.add_item(item)
            if NPlaylistModel.is_favorite(playlist):
                self.load_playlist(playlist)

    def play_song(self, song):
        self._app.player.play(song)

    def play_all(self):
        songs_table = self.ui.songs_table_container.songs_table
        if songs_table is not None:
            self._app.player.set_music_list(songs_table.songs)

    def play_mv(self, mvid):
        pass

    def search_table(self, text):
        songs_table = self.ui.songs_table_container.songs_table
        songs_table.search(text)

    def search_net(self):
        text = self.ui.songs_table_container.table_control.search_box.text()
        self.ui.songs_table_container.hide_info_container()
        if text.strip():
            songs = NSongModel.search(text)
            self._app.message('搜索到 %d 首相关歌曲' % len(songs))
        else:
            songs = None
            self._app.message('搜索内容不能为空')
        if songs:
            self.load_songs(songs)

    def load_songs(self, songs, songs_table=None):
        if songs_table is None:
            songs_table = SongsTable(self._app)
        songs_table.set_songs(songs)
        songs_table.play_song_signal.connect(self.play_song)
        songs_table.download_song_signal.connect(self.downloader.download_song)
        songs_table.play_mv_signal.connect(self.play_mv)
        songs_table.show_artist_signal.connect(self.load_artist)
        songs_table.show_album_signal.connect(self.load_album)
        songs_table.add_song_signal.connect(self._app.player.add_music)
        songs_table.set_to_next_signal.connect(
            self._app.player.set_tmp_fixed_next_song)
        self.ui.songs_table_container.set_table(songs_table)
        self._app.ui.central_panel.right_panel.set_widget(
            self.ui.songs_table_container)

    def load_playlist(self, playlist):
        logger.info('load playlist : %d, %s' % (playlist.pid, playlist.name))
        if playlist.songs is None:
            return
        songs_table = SongsTable(self._app)
        songs_table.set_playlist_id(playlist.pid)
        self.ui.songs_table_container.load_img(playlist.cover_img,
                                               playlist.cover_img_id)
        self.ui.songs_table_container.set_desc(playlist.desc)
        self.load_songs(playlist.songs, songs_table)

    def load_artist(self, aid):
        artist = NArtistModel.get(aid)
        logger.info('load artist: %d, %s' % (aid, artist.name))
        songs = artist.songs
        songs_table = SongsTable(self._app)
        self.ui.songs_table_container.load_img(artist.img,
                                               artist.img_id)
        self.ui.songs_table_container.set_desc(artist.desc)
        self.load_songs(songs, songs_table)

    def load_album(self, bid):
        album = NAlbumModel.get(bid)
        logger.info('load album: %d, %s' % (bid, album.name))
        songs = album.songs
        songs_table = SongsTable(self._app)
        self.ui.songs_table_container.load_img(album.img,
                                               album.img_id)
        self.ui.songs_table_container.set_desc(album.desc)
        self.load_songs(songs, songs_table)

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState\
                or state == QMediaPlayer.PausedState:
            self.ui.show_simi_item()
        else:
            self.ui.hide_simi_item()

    def on_player_media_changed(self, song):
        songs_table = self.ui.songs_table_container.songs_table
        songs_table.scroll_to_song(song)
        api.accumulate_pl_count(song.mid)
