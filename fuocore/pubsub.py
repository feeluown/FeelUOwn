from collections import defaultdict
import logging
from threading import Thread

from fuocore.thread_tcp_server import TcpServer


logger = logging.getLogger(__name__)


class DeadSubscriber(Exception):
    pass


class Subscriber:
    def __init__(self, addr, conn):
        self._addr = addr
        self._conn = conn

    def __eq__(self, obj):
        return self._addr == obj._addr

    def __hash__(self):
        return id(self._addr)


def sendto_subscriber(subscriber, msg):
    try:
        subscriber._conn.send(bytes(msg, 'utf-8'))
    except BrokenPipeError:
        subscriber._conn.close()
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


def handle(conn, addr, gateway, *args, **kwargs):
    """
    NOTE: use tcp instead of udp because some operations need ack
    """
    conn.sendall(b'OK pubsub 1.0\n')
    while True:
        try:
            s = conn.recv(1024).decode('utf-8').strip()
            if not s:
                conn.close()
                break
        except ConnectionResetError:
            logger.debug('Client close the connection.')
            break

        parts = s.split(' ')
        if len(parts) != 2:
            conn.send(b"Invalid command\n")
            continue
        cmd, topic = parts
        if cmd.lower() != 'sub':
            conn.send(bytes("Unknown command '{}'\n".format(cmd.lower()), 'utf-8'))
            continue
        if topic not in gateway.topics:
            conn.send(bytes("Unknown topic '{}'\n".format(topic), 'utf-8'))
            continue
        conn.sendall(bytes('ACK {} {}\n'.format(cmd, topic), 'utf-8'))
        subscriber = Subscriber(addr, conn)
        gateway.link(topic, subscriber)
        break


def create(host='0.0.0.0', port=23334):
    gateway = Gateway()
    server = TcpServer(handle_func=handle, host=host, port=port)
    return gateway, server


def run(gateway, server):
    t = Thread(target=server.run, args=(gateway,), name='TcpServerThread')
    server.thread = t
    t.setDaemon(True)
    t.start()
    host, port = server.host, server.port
    logger.info('Fuo pubsub server running  at {host}:{port}'
                .format(host=host, port=port))
