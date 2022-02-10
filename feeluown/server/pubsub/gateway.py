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

    def publish(self, obj, topic, need_serialize=False):
        # NOTE: use queue? maybe.
        subscribers = self._relations[topic]
        for subscriber in subscribers.copy():
            try:
                if need_serialize is True:
                    msg = serialize('json', obj, brief=False)
                else:
                    msg = obj
                subscriber.write_topic_msg(topic, msg)
            except DeadSubscriber:
                # NOTE: need lock?
                self.remove_subscriber(subscriber)
