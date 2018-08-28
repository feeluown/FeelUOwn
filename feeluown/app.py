import asyncio
import locale
import logging
from functools import partial

from fuocore import LiveLyric, MpvPlayer, Library

from .cliapp import LiveLyricPublisher
from .plugin import PluginsManager
from .version import VersionManager


logger = logging.getLogger(__name__)


class App(object):
    CliMode = 0x0001
    GuiMode = 0x0010

    mode = 0x0000

    def __init__(self, player=None):
        if player is None:
            locale.setlocale(locale.LC_NUMERIC, 'C')
            self.player = MpvPlayer()
            self.player.initialize()
        else:
            self.player = player
        self.playlist = self.player.playlist
        self.library = Library()
        self.live_lyric = LiveLyric()

        self.plugin_mgr = PluginsManager(self)
        self.version_mgr = VersionManager(self)

    def initialize(self):
        self.player.position_changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed)

        self.plugin_mgr.scan()
        loop = asyncio.get_event_loop()
        loop.call_later(10, partial(loop.create_task, self.version_mgr.check_release()))


class CliApp(App):
    mode = App.CliMode

    def __init__(self, pubsub_gateway, player=None):
        super().__init__(player=player)

        self.pubsub_gateway = pubsub_gateway
        self._live_lyric_publisher = LiveLyricPublisher(pubsub_gateway)

        self.live_lyric.sentence_changed.connect(self._live_lyric_publisher.publish)
