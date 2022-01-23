import asyncio
import logging
import sys

from feeluown.server.pubsub import (
    Gateway as PubsubGateway,
    HandlerV1 as PubsubHandlerV1,
    LiveLyricPublisher
)
from feeluown.server.rpc.server import FuoServer
from .app import App


logger = logging.getLogger(__name__)


class ServerApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.server = FuoServer(self)
        self.pubsub_gateway = PubsubGateway()
        self._ll_publisher = LiveLyricPublisher(self.pubsub_gateway)

    def initialize(self):
        super().initialize()
        self.live_lyric.sentence_changed.connect(self._ll_publisher.publish)

    def run(self):
        super().run()

        asyncio.create_task(self.server.run(
            self.get_listen_addr(),
            self.config.RPC_PORT
        ))
        asyncio.create_task(asyncio.start_server(
            PubsubHandlerV1(self.pubsub_gateway).handle,
            host=self.get_listen_addr(),
            port=self.config.PUBSUB_PORT,
        ))

        platform = sys.platform.lower()
        # pylint: disable=import-outside-toplevel
        if platform == 'darwin':
            try:
                from feeluown.nowplaying.global_hotkey_mac import MacGlobalHotkeyManager
            except ImportError as e:
                logger.warning("Can't start mac hotkey listener: %s", str(e))
            else:
                mac_global_hotkey_mgr = MacGlobalHotkeyManager()
                mac_global_hotkey_mgr.start()
        elif platform == 'linux':
            from feeluown.nowplaying.linux import run_mpris2_server
            run_mpris2_server(self)
