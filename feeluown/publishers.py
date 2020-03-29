"""
这个模块存放 Publisher
"""


class LiveLyricPublisher(object):
    topic = 'live_lyric'

    def __init__(self, gateway):
        self.gateway = gateway
        gateway.add_topic(self.topic)

    def publish(self, sentence):
        self.gateway.publish(sentence + '\n', self.topic)
