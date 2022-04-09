import asyncio
import logging
import sys

from aionowplaying import LoopStatus

from feeluown.app.server_app import ServerApp
from feeluown.player import State, PlaybackMode

logger = logging.getLogger(__name__)

try:
    import aionowplaying
except ImportError as e:
    logger.error("can't run now playing server: %s", str(e))
    raise e


class FuoWindowsNowPlayingInterface(aionowplaying.NowPlayingInterface):
    def __init__(self, name, app_: 'ServerApp'):
        self._app = app_
        super(FuoWindowsNowPlayingInterface, self).__init__(name)
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
            self.set_playback_property(aionowplaying.PlaybackPropertyName.LoopStatus, aionowplaying.LoopStatus.Playlist)
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Shuffle, False)
        elif mode == PlaybackMode.one_loop:
            self.set_playback_property(aionowplaying.PlaybackPropertyName.LoopStatus, aionowplaying.LoopStatus.Track)
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Shuffle, False)
        elif mode == PlaybackMode.random:
            self.set_playback_property(aionowplaying.PlaybackPropertyName.LoopStatus, aionowplaying.LoopStatus.Playlist)
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Shuffle, True)
        else:
            self.set_playback_property(aionowplaying.PlaybackPropertyName.LoopStatus, aionowplaying.LoopStatus.None_)
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Shuffle, False)

    def update_song_props(self, meta: dict):
        metadata = aionowplaying.PlaybackProperties.MetadataBean()
        metadata.artist = meta.get('artists', ['Unknown'])
        metadata.album = meta.get('album', '')
        metadata.title = meta.get('title', '')
        metadata.cover = meta.get('artwork', '')
        metadata.url = meta.get('artwork', '')
        metadata.duration = 0
        self._current_meta = metadata
        self.set_playback_property(aionowplaying.PlaybackPropertyName.Metadata, metadata)

    def update_position(self, position):
        if position is not None:
            if self._current_meta is not None and self._current_meta.duration == 0:
                if int((self._app.player.duration or 0) * 1000) > 0:
                    self._current_meta.duration = int((self._app.player.duration or 0) * 1000)
                    self.set_playback_property(aionowplaying.PlaybackPropertyName.Metadata, self._current_meta)
                    self._current_meta = None
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Position, int(position * 1000))

    def update_playback_status(self, state):
        if state == State.stopped:
            status = aionowplaying.PlaybackStatus.Stopped
        elif state == State.paused:
            status = aionowplaying.PlaybackStatus.Paused
        else:
            status = aionowplaying.PlaybackStatus.Playing
        self.set_playback_property(aionowplaying.PlaybackPropertyName.PlaybackStatus, status)

    def on_play(self):
        self._app.player.resume()

    def on_pause(self):
        self._app.player.pause()

    def on_next(self):
        self._app.playlist.next()

    def on_previous(self):
        self._app.playlist.previous()

    def on_loop_status(self, status: LoopStatus):
        if status == LoopStatus.Playlist:
            self._app.playlist.playback_mode = PlaybackMode.loop
        elif status == LoopStatus.Track:
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
    interface = FuoWindowsNowPlayingInterface('FeelUOwn Player', app)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanPlay, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanPause, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanGoNext, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanGoPrevious, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanSeek, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanControl, True)
    await interface.start()
