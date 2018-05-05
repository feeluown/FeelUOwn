import asyncio
import json
import logging
import os
from functools import partial

from PyQt5.QtCore import QObject

from fuocore.netease.provider import NeteaseProvider

from .consts import USER_PW_FILE
from .model import NUserModel
from .ui import Ui


logger = logging.getLogger(__name__)
provider = NeteaseProvider()


class Nem(QObject):

    def __init__(self, app):
        super(Nem, self).__init__(parent=app)
        self._app = app
        self.ui = Ui(self._app)
        self.user = None
        self.init_signal_binding()

    def init_signal_binding(self):
        self.ui.login_btn.clicked.connect(self.ready_to_login)
        self.ui.login_dialog.ok_btn.clicked.connect(self.login)

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
        logger.debug('Trying to load last login user...')
        model = NUserModel.load()
        if model is None:
            logger.debug('Trying to load last login user...failed')
            self.ui.login_dialog.show()
            self.load_user_pw()
        else:
            logger.debug('Trying to load last login user...done')
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

        # app_event_loop = asyncio.get_event_loop()
        # app_event_loop.run_in_executor(
        #     None,
        #     partial(self.ui.login_btn.set_avatar, self.user.img))
        self.user.save()
        self.load_playlists()

    def load_playlists(self):
        self._app.message('正在加载网易云音乐歌单')
        left_panel = self._app.ui.central_panel.left_panel
        user = provider.get_user(self.user.uid)
        left_panel.set_playlists(user.playlists)

    def play_song(self, song):
        logger.debug('Nem request to play song: %s', song)
        self._app.player.play(song.url)

    def play_all(self):
        songs_table = self.ui.songs_table_container.songs_table
        if songs_table is not None:
            self._app.player.playlist.clear()
            for song in songs_table.songs:
                self._app.player.playlist.add(song)

    def play_mv(self, mvid):
        pass

    def load_playlist(self, playlist):
        self._app.ui.show_playlist(playlist)

    def load_artist(self, aid):
        artist = provider.get_artist(aid)
        songs = artist.songs
        self.load_songs(songs)

    def load_album(self, bid):
        album = NAlbumModel.get(bid)
        self.load_songs(album.songs)
