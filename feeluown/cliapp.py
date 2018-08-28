"""
feeluown.cliapp
~~~~~~~~~~~~~~~

It provides a CliMixin to make integration easilly.
"""

import asyncio
import logging
import sys
from collections import defaultdict
from urllib.parse import urlparse

from fuocore.aio_tcp_server import TcpServer
from fuocore import MpvPlayer
from fuocore import LiveLyric
from feeluown.protocol import CmdParser
from feeluown.protocol import exec_cmd

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


async def handle(conn, addr, app, live_lyric):
    event_loop = asyncio.get_event_loop()
    event_loop.sock_sendall(conn, b'OK feeluown 1.0.0\n')
    while True:
        try:
            command = await event_loop.sock_recv(conn, 1024)
        except ConnectionResetError:
            logger.debug('客户端断开连接')
            break
        command = command.decode().strip()
        # NOTE: we will never recv empty byte unless
        # client close the connection
        if not command:
            conn.close()
            break
        logger.debug('RECV: ' + command)
        cmd = CmdParser.parse(command)
        msg = exec_cmd(app, live_lyric, cmd)
        event_loop.sock_sendall(conn, bytes(msg, 'utf-8'))


async def run_server(app, live_lyric, *args, **kwargs):
    port = 23333
    host = '0.0.0.0'
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(
        TcpServer(host, port, handle_func=handle).run(app, live_lyric))
    logger.info('Fuo daemon run in {}:{}'.format(host, port))
