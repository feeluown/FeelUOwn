from collections import defaultdict
import logging

from feeluown.serializers import serialize
from feeluown.server.protocol import DeadSubscriber


logger = logging.getLogger(__name__)


class Gateway:
    def __init__(self):
        self.topics = set()
        self._relations = defaultdict(set)  # {'topic': subscriber_set}

    def add_topic(self, topic):
        self.topics.add(topic)

    def remove_topic(self, topic):
        if topic in self.topics:
            self.topics.remove(topic)

    def link(self, topic, subscriber):
        self._relations[topic].add(subscriber)

    def unlink(self, topic, subscriber):
        if topic in self.topics and subscriber in self._relations[topic]:
            self._relations[topic].remove(subscriber)

    def remove_subscriber(self, subscriber):
        for topic in self.topics:
            if subscriber in self._relations[topic]:
                self._relations[topic].remove(subscriber)

    def publish(self, obj, topic, v2=False):
        # NOTE: use queue? maybe.
        subscribers = self._relations[topic]
        for subscriber in subscribers:
            try:
                if v2 is True:
                    msg = serialize('json', obj, brief=False)
                else:
                    msg = serialize('plain', obj, brief=False)
                subscriber.write_topic_msg(topic, msg, '2.0' if v2 else '1.0')
            except DeadSubscriber:
                # NOTE: need lock?
                self.remove_subscriber(subscriber)
