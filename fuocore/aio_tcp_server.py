import asyncio
import logging
import socket


logger = logging.getLogger(__name__)


class TcpServer(object):
    """A simple asyncio TCP server"""

    def __init__(self, host, port, handle_func):
        self.host = host
        self.port = port
        self.handle_func = handle_func

        self._sock = None

    async def run(self, *args, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen()
        # make restart easier
        sock.setblocking(0)
        self._sock = sock

        event_loop = asyncio.get_event_loop()
        while True:
            conn, addr = await event_loop.sock_accept(sock)
            event_loop.create_task(
                self.handle_func(conn, addr, *args, **kwargs))
