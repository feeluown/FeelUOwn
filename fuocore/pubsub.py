from collections import defaultdict
import logging


logger = logging.getLogger(__name__)


class DeadSubscriber(Exception):
    pass


class Subscriber:
    def __init__(self, addr, conn):
        self._addr = addr
        self.writer = conn

    def __eq__(self, obj):
        return self._addr == obj._addr

    def __hash__(self):
        return id(self._addr)


def sendto_subscriber(subscriber, msg):
    try:
        subscriber.writer.write(bytes(msg, 'utf-8'))
    except BrokenPipeError:
        subscriber.writer.close()
        del subscriber
        raise DeadSubscriber


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

    def publish(self, msg, topic):
        # NOTE: use queue? maybe.
        subscribers = self._relations[topic]
        for subscriber in subscribers:
            try:
                sendto_subscriber(subscriber, msg)
            except DeadSubscriber:
                # NOTE: need lock?
                self._relations[topic].remove(subscriber)
                break


class HandlerV1:
    """
    pubsub protocol 1.0
    -------------------

    we only handle one request::

        sub <topic>

    For example::

        sub topic.live_lyric  # deprecated

    The response will be a line ends with \r\n::

        Oops <err_msg>        # failed
        OK                    # ok
    """
    def __init__(self, gateway):
        self.gateway = gateway

    async def handle(self, reader, writer):
        gateway = self.gateway

        # send pubsub server version info
        writer.write(b'OK pubsub 1.0\r\n')
        while True:
            try:
                line = await reader.readline()
            except ConnectionResetError:
                logger.debug('Client close the connection.')
                break

            if line == b'':  # connection closed
                writer.close()
                break

            # handle `sub <topic>` command
            err = 'Oops {reason}'
            reason = None
            try:
                cmd, topic = line.decode('utf-8').strip().split(' ')
            except ValueError:
                reason = 'invalid request'
            else:
                if cmd.lower() != 'sub':
                    reason = 'unknown command'
                else:
                    if topic.startswith('topic.'):
                        topic = topic[6:]
                    if topic not in gateway.topics:
                        reason = "unknown topic '{}'".format(topic)
            if reason is not None:
                msg = err.format(reason=reason)
                writer.write(bytes(msg, 'utf-8'))
                writer.write(b'\r\n')
                continue
            else:
                writer.write(b'OK\r\n')
                peername = writer.get_extra_info('peername')
                subscriber = Subscriber(peername, writer)
                gateway.link(topic, subscriber)
                break
