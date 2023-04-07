import logging

import aionowplaying as aionp

from feeluown.app.server_app import ServerApp
from feeluown.player import State, PlaybackMode

logger = logging.getLogger(__name__)


PlayProp = aionp.PlaybackPropertyName


class FuoWindowsNowPlayingService(aionp.NowPlayingInterface):
    def __init__(self, name, app_: 'ServerApp'):
        self._app = app_
        super(FuoWindowsNowPlayingService, self).__init__(name)
        self._app.player.position_changed.connect(self.update_position)
        self._app.player.state_changed.connect(self.update_playback_status)
        self._app.player.metadata_changed.connect(self.update_song_props)
        self._app.playlist.playback_mode_changed.connect(self.update_playback_mode)
        self.update_playback_mode(self._app.playlist.playback_mode)
        self._current_meta = None

    def update_playback_mode(self, mode: PlaybackMode):
        if mode is None:
            return
        if mode == PlaybackMode.loop:
            self.set_playback_property(PlayProp.LoopStatus, aionp.LoopStatus.Playlist)
            self.set_playback_property(PlayProp.Shuffle, False)
        elif mode == PlaybackMode.one_loop:
            self.set_playback_property(PlayProp.LoopStatus, aionp.LoopStatus.Track)
            self.set_playback_property(PlayProp.Shuffle, False)
        elif mode == PlaybackMode.random:
            self.set_playback_property(PlayProp.LoopStatus, aionp.LoopStatus.Playlist)
            self.set_playback_property(PlayProp.Shuffle, True)
        else:
            self.set_playback_property(PlayProp.LoopStatus, aionp.LoopStatus.None_)
            self.set_playback_property(PlayProp.Shuffle, False)

    def update_song_props(self, meta: dict):
        metadata = aionp.PlaybackProperties.MetadataBean()
        metadata.artist = meta.get('artists', ['Unknown'])
        metadata.album = meta.get('album', '')
        metadata.title = meta.get('title', '')
        metadata.cover = meta.get('artwork', '')
        metadata.url = meta.get('artwork', '')
        metadata.duration = 0
        self._current_meta = metadata
        self.set_playback_property(PlayProp.Metadata, metadata)

    def update_position(self, position):
        if position is not None:
            if self._current_meta is not None and self._current_meta.duration == 0:
                if int((self._app.player.duration or 0) * 1000) > 0:
                    self._current_meta.duration = int(
                        (self._app.player.duration or 0) * 1000
                    )
                    self.set_playback_property(PlayProp.Metadata, self._current_meta)
                    self._current_meta = None
            self.set_playback_property(PlayProp.Position, int(position * 1000))

    def update_playback_status(self, state):
        if state == State.stopped:
            status = aionp.PlaybackStatus.Stopped
        elif state == State.paused:
            status = aionp.PlaybackStatus.Paused
        else:
            status = aionp.PlaybackStatus.Playing
        self.set_playback_property(PlayProp.PlaybackStatus, status)

    def on_play(self):
        self._app.player.resume()

    def on_pause(self):
        self._app.player.pause()

    def on_next(self):
        self._app.playlist.next()

    def on_previous(self):
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
        self._app.player.position = int(offset / 1000)

    def __del__(self):
        self.stop()


async def run_nowplaying_server(app):
    service = FuoWindowsNowPlayingService('FeelUOwn Player', app)
    service.set_playback_property(PlayProp.CanPlay, True)
    service.set_playback_property(PlayProp.CanPause, True)
    service.set_playback_property(PlayProp.CanGoNext, True)
    service.set_playback_property(PlayProp.CanGoPrevious, True)
    service.set_playback_property(PlayProp.CanSeek, True)
    service.set_playback_property(PlayProp.CanControl, True)
    await service.start()
