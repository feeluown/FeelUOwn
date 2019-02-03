import asyncio
import logging
from functools import partial
from contextlib import contextmanager

from fuocore import LiveLyric, Library
from fuocore.pubsub import run as run_pubsub

from .protocol import FuoProcotol
from .player import Player
from .plugin import PluginsManager
from .publishers import LiveLyricPublisher
from .request import Request
from .version import VersionManager


logger = logging.getLogger(__name__)


class App:
    CliMode = 0x0001
    GuiMode = 0x0010

    # mode = 0x0000
    mode = CliMode

    def __init__(self, player_kwargs=None):
        super().__init__()
        self.player = Player(app=self, **(player_kwargs or {}))
        self.playlist = self.player.playlist
        self.library = Library()
        self.live_lyric = LiveLyric()
        self.protocol = FuoProcotol(self)
        self.plugin_mgr = PluginsManager(self)
        self.version_mgr = VersionManager(self)
        self.request = Request(self)
        self._g = {}

    def initialize(self):
        self.player.position_changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed)
        self.plugin_mgr.scan()

        self.pubsub_gateway, self.pubsub_server = run_pubsub()
        self.protocol.run_server()

        self._ll_publisher = LiveLyricPublisher(self.pubsub_gateway)
        self.live_lyric.sentence_changed.connect(self._ll_publisher.publish)
        loop = asyncio.get_event_loop()
        loop.call_later(10, partial(loop.create_task, self.version_mgr.check_release()))

    def exec_(self, code):
        obj = compile(code, '<string>', 'single')
        self._g.update({
            'app': self,
            'player': self.player
        })
        exec(obj, self._g, self._g)

    def show_msg(self, msg, *args, **kwargs):
        logger.info(msg)

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

    def shutdown(self):
        self.pubsub_server.close()
        self.player.stop()
        self.player.shutdown()
