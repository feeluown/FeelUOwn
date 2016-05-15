import logging
from feeluown.player_mode import PlayerModeBase

from .model import NUserModel


logger = logging.getLogger(__name__)


class FM_mode(PlayerModeBase):
    def __init__(self, app):
        super().__init__(app)
        self.player = app.player
        self._name = 'FM'
        self._songs = []

    @property
    def name(self):
        return self._name

    def on_playlist_finished(self):
        logger.debug('fm mode: playlist finished')
        song = self._get_song()
        self.player.other_mode_play(song)

    def load(self):
        self.player.stop()
        song = self._get_song()
        if song is not None:
            self.player.other_mode_play(song)
        else:
            self.unload()

    def _get_song(self):
        if not self._songs:
            self._songs = NUserModel.get_fm_song()
        song = self._songs.pop(0)
        return song
