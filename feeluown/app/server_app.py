import asyncio
import logging

from feeluown.server.pubsub import (
    Gateway as PubsubGateway,
    LiveLyricPublisher,
)
from feeluown.server.pubsub.publishers import SignalPublisher
from feeluown.server import FuoServer, ProtocolType
from feeluown.nowplaying import run_nowplaying_server
from .app import App

logger = logging.getLogger(__name__)


class ServerApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rpc_server = FuoServer(self, ProtocolType.rpc)
        self.pubsub_server = FuoServer(self, ProtocolType.pubsub)
        self.pubsub_gateway = PubsubGateway()
        self._ll_publisher = LiveLyricPublisher(self.pubsub_gateway)
        self._signal_publish = SignalPublisher(self.pubsub_gateway)

    def initialize(self):
        super().initialize()
        self.live_lyric.sentence_changed.connect(self._ll_publisher.publish)

        signals = [
            (self.player.metadata_changed, 'player.metadata_changed'),
            (self.player.seeked, 'player.seeked'),
            (self.player.state_changed, 'player.state_changed'),
            (self.player.duration_changed, 'player.duration_changed'),
            (self.live_lyric.sentence_changed, 'live_lyric.sentence_changed'),
        ]
        for signal, name in signals:
            self.pubsub_gateway.add_topic(name)
            signal.connect(self._signal_publish.on_emitted(name),
                           weak=False,
                           aioqueue=True)

    def run(self):
        super().run()

        asyncio.create_task(
            self.rpc_server.run(self.get_listen_addr(), self.config.RPC_PORT))
        asyncio.create_task(
            self.pubsub_server.run(
                self.get_listen_addr(),
                self.config.PUBSUB_PORT,
            ))
        if self.config.ENABLE_WEB_SERVER:
            try:
                from feeluown.webserver import run_web_server
            except ImportError as e:
                logger.error(f"can't enable webserver, err: {e}")
            else:
                asyncio.create_task(
                    run_web_server(self.get_listen_addr(), self.config.WEB_PORT))
        asyncio.create_task(run_nowplaying_server(self))
