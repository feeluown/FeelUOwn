import asyncio
import logging

from .parser import Parser
from .excs import FuoSyntaxError
from .data_structure import Response


logger = logging.getLogger(__name__)


class RequestError(Exception):
    pass


async def read_request(reader):
    """读取一个请求

    读取成功时，返回 Request 对象，如果读取失败（比如客户端关闭连接），
    则返回 None。其它异常会抛出 RequestError。

    :type reader: asyncio.StreamReader
    """
    try:
        line_bytes = await reader.readline()
    except ValueError as e:
        raise RequestError('request size should be less than 64KiB') from e
    if not line_bytes:  # EOF
        return None
    line_text = line_bytes.decode('utf-8').strip()
    if not line_text:
        return 0
    req = None
    try:
        req = Parser(line_text).parse()
    except FuoSyntaxError as e:
        raise RequestError(e.human_readabe_msg) from e
    else:
        if not req.has_heredoc:
            return req
        word_bytes = bytes(req.heredoc_word, 'utf-8')
        buf = bytearray()
        while 1:
            line_bytes = await reader.readline()
            if line_bytes[-2:] == b'\r\n':
                stripped_line_bytes = line_bytes[:-2]
            else:
                stripped_line_bytes = line_bytes[:-1]
            if stripped_line_bytes == word_bytes:
                break
            else:
                buf.extend(line_bytes)
            if len(buf) >= 2 ** 16:
                raise RequestError('heredoc body should be less than 64KiB')
        req.set_heredoc_body(bytes(buf).decode('utf-8'))
    return req


class FuoServerProtocol(asyncio.streams.FlowControlMixin):
    """asyncio-style fuo server protocol (ClientHandler)

    Implementation references:
    - asyncio.streams.StreamReaderProtocol
    - aiohttp.web_protocol.RequestHandler

    TODO:
    - add request timeout: close connection if no action happens
    - add graceful shutdown: close connection before exit
    """
    def __init__(self, handle_req, loop):
        super().__init__(loop)
        self._handle_req = handle_req
        self._loop = loop

        # StreamReader provides some convinient file-object-like methods
        # like readline, which is really useful for our implementation.
        self._reader = None  # type: asyncio.StreamReader
        self._writer = None

        self._peername = None

    async def read_request(self):
        return await read_request(self._reader)

    async def write_response(self, resp):
        # TODO: 区分客户端和服务端错误（比如客户端错误后面加 ! 标记）
        msg_bytes = bytes(resp.text, 'utf-8')
        response_line = ('ACK {} {}\r\n'
                         .format(resp.code, len(msg_bytes)))
        self._writer.write(bytes(response_line, 'utf-8'))
        self._writer.write(msg_bytes)
        self._writer.write(b'\r\n')
        await self._writer.drain()

    async def start(self):
        """connection handler"""
        # we should call drain after each write to do flow control,
        # though it is not so important in this case.
        try:
            self._writer.write(b'OK fuo 3.0\r\n')
            await self._writer.drain()
            while not self._connection_lost:
                try:
                    req = await self.read_request()
                except RequestError as e:
                    msg = 'bad reqeust!\r\n' + str(e)
                    bad_request_resp = Response(ok=False, text=msg)
                    await self.write_response(bad_request_resp)
                else:
                    if req is None:  # client close the connection
                        break
                    elif req == 0:  # ignore the empty request
                        continue
                    # 通常来说，客户端如果想断开连接，只需要自己主动关闭连接即可，
                    # 但如果客户端不方便主动断开，可以发送 quit 命令，
                    # 让服务端来主动关闭连接。
                    #
                    # 客户端不方便主动断开的例子：当用户使用 NetCat 发送请求时，
                    # 用户想在读取完一个 fuo 响应后断开。
                    if req.cmd == 'quit':
                        # FIXME: 理论上最好能等待 close 结束
                        self._writer.close()
                    else:
                        resp = self._handle_req(req)
                        await self.write_response(resp)
        except ConnectionResetError:
            # client close the connection
            pass

    def connection_made(self, transport):
        self._peername = transport.get_extra_info('peername')
        logger.debug('%s connceted to fuo daemon.', self._peername)
        self._reader = asyncio.StreamReader(loop=self._loop)
        self._writer = asyncio.StreamWriter(
            transport, self, self._reader, self._loop)
        # Unlike aiohttp RequestHandler, we will never cancel the handler task,
        # our task should die when it is supposed to. For instance, when the
        # client close the connection, connection lost with ConnectionResetErrror,
        # the handler task should catch the exc and exit.
        self._loop.create_task(self.start())

    def connection_lost(self, exc):
        """called when our transport is closed"""
        if self._reader is not None:
            if exc is None:
                self._reader.feed_eof()
            else:
                self._reader.set_exception(exc)
        super().connection_lost(exc)
        # HELP: if you dive into aiohttp RequestHandler or StreamReaderProtocol,
        # you can see that they set reader, writer...almost
        # every thing to None when connection lost. I just dont know why.
        # I have done some experiment, the reader and writer can be
        # gc-collected even if we do not set it to None manually.
        # they can be deleted after protocol(self) is deleted.
        self._reader = None
        self._writer = None
        logger.debug('%s disconnceted from fuo daemon.', self._peername)

    def data_received(self, data):
        self._reader.feed_data(data)

    def eof_received(self):
        """client has written eof

        Explaination: this means the client will send no more data,
        client has close the socket or shutdown with SHUT_WR/SHUT_RDWR flag.
        If we use tcpdump to do packet capture, we can see a FIN packet.

        For fuo protocol, if client shutdown the write pipe, we believe that
        the client is closing the socket, we will just close the socket,
        send no data any more, even if the last response may not complete.
        """
        return False
