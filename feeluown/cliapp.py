"""
feeluown.cliapp
~~~~~~~~~~~~~~~

It provides a CliMixin to make integration easilly.
"""


import logging

from fuocore.live_lyric import LiveLyric


logger = logging.getLogger(__name__)


class LiveLyricPublisher(object):
    topic = 'topic.live_lyric'

    def __init__(self, gateway):
        self.gateway = gateway
        gateway.add_topic(self.topic)

    def publish(self, sentence):
        self.gateway.publish(sentence + '\n', self.topic)


class CliAppMixin(object):
    """
    FIXME: Subclass must call init to make this mixin
    work properly, which seems to be little bit strange. But
    this mixin helps avoid duplicate code temporarily.
    """
    def __init__(self):
        live_lyric = LiveLyric()
        live_lyric_publisher = LiveLyricPublisher(self.pubsub_gateway)

        self.live_lyric = live_lyric
        self._live_lyric_publisher = live_lyric_publisher

        live_lyric.sentence_changed.connect(live_lyric_publisher.publish)
        self.player.position_changed.connect(live_lyric.on_position_changed)
        self.playlist.song_changed.connect(live_lyric.on_song_changed)
