import asyncio
import logging
import re

from fuocore.aio_tcp_server import TcpServer
from fuocore.cmds import interprete

logger = logging.getLogger(__name__)


class FuoServer:
    def __init__(self, *, library, player, playlist, live_lyric):
        self._library = library
        self._player = player
        self._playlist = playlist
        self._live_lyric = live_lyric

    def run(self, host='0.0.0.0', port=23333):
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(
            TcpServer(host, port, handle_func=self.handle_conn).run())
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    async def handle_conn(self, conn, addr):
        event_loop = asyncio.get_event_loop()
        await event_loop.sock_sendall(conn, b'OK feeluown 1.0.0\n')
        while True:
            command = b''
            try:
                max_bytes = 1024 * 1024
                per_bytes = 256
                while len(command) < max_bytes:
                    part = await event_loop.sock_recv(conn, per_bytes)
                    command += part
                    if len(part) < per_bytes:
                        break
                else:
                    logger.warning('The length of command should be less than 1K')
            except ConnectionResetError:
                logger.debug('客户端断开连接')
                break
            command = command.decode()
            # NOTE: we will never recv empty byte unless
            # client close the connection
            if not command:
                conn.close()
                break
            logger.debug('RECV: %s', command)
            msg = interprete(command,
                             library=self._library,
                             player=self._player,
                             playlist=self._playlist,
                             live_lyric=self._live_lyric)
            await event_loop.sock_sendall(conn, bytes(msg, 'utf-8'))
