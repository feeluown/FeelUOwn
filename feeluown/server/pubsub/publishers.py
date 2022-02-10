from functools import partial

from .gateway import Gateway


class LiveLyricPublisher:
    topic = 'live_lyric'

    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        gateway.add_topic(self.topic)

    def publish(self, sentence):
        self.gateway.publish(sentence + '\n', self.topic)


class SignalPublisher:
    def __init__(self, gateway: Gateway):
        self.gateway = gateway

    def on_emitted(self, name):
        return partial(self.publish, name)

    def publish(self, name, *args):
        self.gateway.publish(list(args), name, need_serialize=True)
