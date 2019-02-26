# -*- coding: utf-8 -*-

import logging

from fuocore.player import MpvPlayer, Playlist as _Playlist


logger = logging.getLogger(__name__)


class Playlist(_Playlist):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

    @_Playlist.current_song.setter
    def current_song(self, song):
        """如果歌曲 url 无效，则尝试从其它平台找一个替代品"""
        if song is None or song.url:
            _Playlist.current_song.fset(self, song)
            return
        self.mark_as_bad(song)
        logger.info('Song:%s is invalid, try to get standby', song)
        songs = self._app.library.list_song_standby(song)
        if songs:
            song = songs[0]
        _Playlist.current_song.fset(self, song)


class Player(MpvPlayer):

    def __init__(self, app, *args, **kwargs):
        super().__init__(playlist=Playlist(app), *args, **kwargs)
        self._app = app
        self.initialize()

    def play_video(self, video):
        pass
