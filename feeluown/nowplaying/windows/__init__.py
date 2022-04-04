import asyncio
import logging
import sys

from feeluown.app.server_app import ServerApp
from feeluown.player import State

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

    def update_song_props(self, meta: dict):
        metadata = aionowplaying.PlaybackProperties.MetadataBean()
        metadata.artist = meta.get('artists', ['Unknown'])
        metadata.album = meta.get('album', '')
        metadata.title = meta.get('title', '')
        metadata.cover = meta.get('artwork', '')
        metadata.url = meta.get('artwork', '')
        metadata.duration = int((self._app.player.duration or 0) * 1000)
        self.set_playback_property(aionowplaying.PlaybackPropertyName.Metadata, metadata)

    def update_position(self, position):
        if position is not None:
            self.set_playback_property(aionowplaying.PlaybackPropertyName.Position, int(position * 1000))

    def update_playback_status(self, state):
        if state == State.stopped:
            status = aionowplaying.PlaybackStatus.Stopped
        elif state == State.paused:
            status = aionowplaying.PlaybackStatus.Paused
        else:
            status = aionowplaying.PlaybackStatus.Playing
        self.set_playback_property(aionowplaying.PlaybackPropertyName.PlaybackStatus, status)

    async def on_play(self):
        self._app.player.resume()

    async def on_pause(self):
        self._app.player.pause()

    async def on_next(self):
        self._app.playlist.next()

    async def on_previous(self):
        self._app.playlist.previous()

    def __del__(self):
        self.stop()


async def run_nowplaying_server(app):
    interface = FuoWindowsNowPlayingInterface('FeelUOwn Player', app)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanPlay, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanPause, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanGoNext, True)
    interface.set_playback_property(aionowplaying.PlaybackPropertyName.CanGoPrevious, True)
    await interface.start()
