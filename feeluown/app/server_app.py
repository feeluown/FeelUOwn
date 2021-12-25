from feeluown.pubsub import Gateway as PubsubGateway, LiveLyricPublisher
from feeluown.rpc.server import FuoServer
from .app import App


class ServerApp(App):
    def __init__(self, config):
        super().__init__(config)

        self.server = FuoServer(self)
        self.pubsub_gateway = PubsubGateway()
        self._ll_publisher = LiveLyricPublisher(self.pubsub_gateway)

    def initialize(self):
        if self.mode & self.DaemonMode:
            self.live_lyric.sentence_changed.connect(self._ll_publisher.publish)
