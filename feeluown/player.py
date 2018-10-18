# -*- coding: utf-8 -*-
import locale
import logging

from fuocore.player import MpvPlayer


logger = logging.getLogger(__name__)


class Player(MpvPlayer):

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self.initialize()

    def play_song(self, song):
        if not song.url:
            msg = 'Searching {} standby'.format(song)
            with self._app.create_action(msg) as action:
                action.set_progress(0.2)
                songs = self._app.library.list_song_standby(song)
                if songs:
                    song = songs[0]
                else:
                    action.failed()
        with self._app.create_action('play {}'.format(song)):
            super().play_song(song)
