import asyncio
import locale
import logging
from functools import partial
from contextlib import contextmanager

from fuocore import LiveLyric, MpvPlayer, Library

from feeluown.protocol import FuoProcotol
from .cliapp import LiveLyricPublisher
from .player import Player
from .plugin import PluginsManager
from .version import VersionManager


logger = logging.getLogger(__name__)


class App(object):
    CliMode = 0x0001
    GuiMode = 0x0010

    mode = 0x0000

    def __init__(self, player_kwargs=None):
        self.player = Player(app=self, **(player_kwargs or {}))
        self.playlist = self.player.playlist
        self.library = Library()
        self.live_lyric = LiveLyric()

        self.protocol = FuoProcotol(self)

        self.plugin_mgr = PluginsManager(self)
        self.version_mgr = VersionManager(self)

    def show_msg(self, msg, *args, **kwargs):
        logger.info(msg)

    def initialize(self):
        self.player.position_changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed)

        self.plugin_mgr.scan()
        loop = asyncio.get_event_loop()
        loop.call_later(10, partial(loop.create_task, self.version_mgr.check_release()))

    @contextmanager
    def create_action(self, s):
        show_msg = self.show_msg

        class Action:
            def set_progress(self, value):
                value = int(value * 100)
                show_msg(s + '...{}%'.format(value), timeout=-1)

            def failed(self):
                show_msg(s + '...failed', timeout=-1)

        show_msg(s + '...', timeout=-1)  # doing
        try:
            yield Action()
        except Exception:
            show_msg(s + '...error')  # error
            raise
        else:
            show_msg(s + '...done')  # done


class CliApp(App):
    mode = App.CliMode

    def __init__(self, pubsub_gateway, player_kwargs=None):
        super().__init__(player_kwargs=player_kwargs)

        self.pubsub_gateway = pubsub_gateway
        self._live_lyric_publisher = LiveLyricPublisher(pubsub_gateway)

        self.live_lyric.sentence_changed.connect(self._live_lyric_publisher.publish)
