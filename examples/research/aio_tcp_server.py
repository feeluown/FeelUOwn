import asyncio
import logging
import socket


logger = logging.getLogger(__name__)


class TcpServer(object):
    """A simple asyncio TCP server

    This implementation is based on low-level event loop APIs such as
    `loop.sock_accept`, `loop.sock_sendall`, and `loop.sock_recv`.

    Asyncio also provides `loop.create_server` for creating a server, together with
    `StreamReader` and `StreamWriter` for I/O, which is overall a more high-level
    abstraction. `StreamReader` wraps convenient methods such as `readline` and
    `readuntil`, making it easier to use.

    `StreamWriter` maintains its own internal buffer, so calling `write()` does not
    immediately send data to the operating system. Prior to Python 3.7, there was
    no particularly good way to reliably ensure this behavior. However, it does
    provide a `drain()` method to flush part of the buffered data to the OS.

    Overall, I personally prefer this `TcpServer` implementation. Its interface is
    very explicit and feels much closer to using blocking sockets. The asyncio
    stream-based API, on the other hand, is less intuitive to me. That said, the
    current implementation in FeelUOwn does use asyncio streams—probably due to a
    bit of personal perfectionism.
    """

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
