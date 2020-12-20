import asyncio
import logging
import socket


logger = logging.getLogger(__name__)


class TcpServer(object):
    """A simple asyncio TCP server

    使用 loop 的 sock_accept/sock_sendall/sock_recv 等方法来实现，
    这些方法相对都比较 low-level。

    asyncio 也提供了 ``loop.create_server`` 方法创建一个 server，然后使用
    StreamReader 和 StreamWriter 来进行读写，整体来说更加 high level。
    StreamReader 封装了类似 readline/readuntil 等方法，使用起来很方便。
    StreamWriter 有一个自己的 buffer，所以调用 write 方法时，
    它没有真正的将数据写给操作系统，在 3.7 之前，它似乎都没有很好的办法来确保这一点。
    不过它有个 drain 方法来将 buffer 中的一部分数据 flush 到操作系统。

    总体来说，个人目前更喜欢这个 TcpServer 的实现，接口非常明确，
    和阻塞的 socket 使用起来特别像。而 asyncio 提供的那一套用起来不直观，
    不过现在 feeluown 中使用的正是 asyncio 这一套，大概是强迫症。
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
