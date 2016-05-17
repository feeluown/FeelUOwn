import logging
from feeluown.player_mode import PlayerModeBase

from .consts import SONG_SOURCE


logger = logging.getLogger(__name__)


class Simi_mode(PlayerModeBase):
    def __init__(self, app):
        super().__init__(app)
        self._app = app
        self.player = app.player
        self._name = 'SIMI'
        self._songs = []

    @property
    def name(self):
        return self._name

    def on_playlist_finished(self):
        logger.debug('simi mode: playlist finished')
        song = self._get_song()
        self.player.other_mode_play(song)

    def load(self):
        song = self._get_song()
        if song is not None:
            self.player.other_mode_play(song)
        else:
            self._app.message('当前播放歌曲不是网易云音乐歌曲', error=True)
            logger.warning('cant enter simi mode')
            # TODO: when PlayerModeManager call exit_to_normal, it call unload
            #       again
            self.unload()

    def _get_song(self):
        if not self._songs:
            song = self._check_player_song()
            if song is not None:
                self._songs = song.get_simi_songs()
            else:
                return None
        song = self._songs.pop(0)
        return song

    def _check_player_song(self):
        song = self.player.current_song
        if song is not None and song.source == SONG_SOURCE:
            return song
        return None
