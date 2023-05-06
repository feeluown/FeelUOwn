# pylint: disable=import-error
import logging

import aionowplaying as aionp

from feeluown.app.server_app import ServerApp
from feeluown.player import State, PlaybackMode

logger = logging.getLogger(__name__)
PlayProp = aionp.PlaybackPropertyName
StatePlaybackStatusMapping = {
    State.stopped: aionp.PlaybackStatus.Stopped,
    State.paused: aionp.PlaybackStatus.Paused,
    State.playing: aionp.PlaybackStatus.Playing,
}
PlaybackStatusStateMapping = {
    v: k
    for k, v in StatePlaybackStatusMapping.items()
}


def to_aionp_time(t):
    return int(t * 1000)


def from_aionp_time(t):
    return t / 1000


class NowPlayingService(aionp.NowPlayingInterface):
    def __init__(self, app: 'ServerApp'):
        super().__init__('FeelUOwn')
        self._app = app

        self._app.player.seeked.connect(self.update_position)
        self._app.player.media_loaded.connect(self.on_player_media_loaded,
                                              aioqueue=True)
        self._app.player.duration_changed.connect(self.update_duration,
                                                  aioqueue=True)
        self._app.player.state_changed.connect(self.update_playback_status)
        self._app.player.metadata_changed.connect(self.update_song_metadata,
                                                  aioqueue=True)
        self._app.player.media_changed.connect(self.on_player_media_changed,
                                               aioqueue=True)
        self._app.playlist.playback_mode_changed.connect(
            self.update_playback_mode)
        self._app.started.connect(lambda: self.update_playback_mode(
            self._app.playlist.playback_mode))

        self.set_playback_property(PlayProp.CanPlay, True)
        self.set_playback_property(PlayProp.CanPause, True)
        self.set_playback_property(PlayProp.CanGoNext, True)
        self.set_playback_property(PlayProp.CanGoPrevious, True)
        self.set_playback_property(PlayProp.CanSeek, True)
        self.set_playback_property(PlayProp.CanControl, True)

    def update_playback_mode(self, mode: PlaybackMode):
        mode_mapping = {
            PlaybackMode.loop: (aionp.LoopStatus.Playlist, False),
            PlaybackMode.one_loop: (aionp.LoopStatus.Track, False),
            PlaybackMode.random: (aionp.LoopStatus.Playlist, True),
            PlaybackMode.sequential: (aionp.LoopStatus.None_, False),
        }
        mode_value = mode_mapping.get(mode)
        self.set_playback_property(PlayProp.LoopStatus, mode_value[0])
        self.set_playback_property(PlayProp.Shuffle, mode_value[1])

    def update_song_metadata(self, meta: dict):
        metadata = aionp.PlaybackProperties.MetadataBean()
        metadata.artist = meta.get('artists', ['Unknown'])
        metadata.album = meta.get('album', '')
        metadata.title = meta.get('title', '')
        metadata.cover = meta.get('artwork', '')
        metadata.url = ''
        self.set_playback_property(PlayProp.Metadata, metadata)

    def update_duration(self, duration):
        self.set_playback_property(PlayProp.Duration, int(duration * 1000))

    def update_position(self, position):
        self.set_playback_property(PlayProp.Position, int(position * 1000))

    def update_playback_status(self, state):
        self.set_playback_property(PlayProp.PlaybackStatus,
                                   StatePlaybackStatusMapping[state])

    async def on_play(self):
        self._app.player.resume()

    async def on_pause(self):
        self._app.player.pause()

    async def on_next(self):
        self._app.playlist.next()

    async def on_previous(self):
        self._app.playlist.previous()

    def on_loop_status(self, status: aionp.LoopStatus):
        if status == aionp.LoopStatus.Playlist:
            self._app.playlist.playback_mode = PlaybackMode.loop
        elif status == aionp.LoopStatus.Track:
            self._app.playlist.playback_mode = PlaybackMode.one_loop
        else:
            self._app.playlist.playback_mode = PlaybackMode.sequential

    def on_shuffle(self, shuffle: bool):
        if shuffle:
            self._app.playlist.playback_mode = PlaybackMode.random
        else:
            self._app.playlist.playback_mode = PlaybackMode.sequential

    def on_seek(self, offset: int):
        self._app.player.position = from_aionp_time(offset)

    def get_playback_property(self, name: PlayProp):
        if name == PlayProp.Duration:
            return to_aionp_time(self._app.player.duration)
        elif name == PlayProp.Position:
            return to_aionp_time(self._app.player.position)
        elif name == PlayProp.PlaybackStatus:
            return StatePlaybackStatusMapping[self._app.player.state]
        elif name == PlayProp.Rate:
            return 1.0
        else:
            raise ValueError('unknown key')

    def on_player_media_changed(self, _):
        # Update position when media is changed, so that some nowplaying servers
        # can update its UI immediately.
        self.set_playback_property(PlayProp.Position, 0)

    def on_player_media_loaded(self):
        # As seeked signal is not emitted when media is changed,
        # update position explicitly.
        self.set_playback_property(PlayProp.Position, 0)
