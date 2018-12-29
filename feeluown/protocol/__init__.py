import asyncio
import logging

from fuocore.aio_tcp_server import TcpServer

from .handlers import (
    HelpHandler,
    SearchHandler,
    PlayerHandler,
    PlaylistHandler,
    StatusHandler,
)

from .show import ShowHandler  # noqa
from .parser import CmdParser  # noqa


logger = logging.getLogger(__name__)


def exec_cmd(app, live_lyric, cmd):
    # FIXME: 要么只传 app，要么把 player, live_lyric 等分别传进来
    # 目前更使用 app 作为参数

    logger.debug('EXEC_CMD: ' + str(cmd))

    # 一些
    if cmd.action in ('help', ):
        handler = HelpHandler(app,
                              live_lyric=live_lyric)

    elif cmd.action in ('show', ):
        handler = ShowHandler(app,
                              live_lyric=live_lyric)

    elif cmd.action in ('search', ):
        handler = SearchHandler(app,
                                live_lyric=live_lyric)

    # 播放器相关操作
    elif cmd.action in (
        'play', 'pause', 'resume', 'stop', 'toggle',
    ):
        handler = PlayerHandler(app,
                                live_lyric=live_lyric)

    # 播放列表相关命令
    elif cmd.action in (
        'add', 'remove', 'clear', 'list',
        'next', 'previous',
    ):
        """
        add/remove fuo://local:song:xxx
        create xxx

        set playback_mode=random
        set volume=100
        """
        handler = PlaylistHandler(app,
                                  live_lyric=live_lyric)
    elif cmd.action in ('status',):
        handler = StatusHandler(app,
                                live_lyric=live_lyric)
    else:
        return 'Oops Command not found!\n'

    rv = 'ACK {}'.format(cmd.action)
    if cmd.args:
        rv += ' {}'.format(' '.join(cmd.args))
    try:
        cmd_rv = handler.handle(cmd)
        if cmd_rv:
            rv += '\n' + cmd_rv
    except Exception as e:
        logger.exception('handle cmd({}) error'.format(cmd))
        return '\nOops\n'
    else:
        rv = rv or ''
        return rv + '\nOK\n'


class FuoProcotol:
    """fuo 控制协议

    TODO: 将这个类的实现移到另外一个模块，而不是放在 __init__.py 中
    TODO: 将命令的解析逻辑放在这个类里来实现
    """
    def __init__(self, app):
        self._app = app
        self._library = app.library
        self._live_lyric = app.live_lyric

    async def handle(self, conn, addr):
        app = self._app
        live_lyric = self._live_lyric

        event_loop = asyncio.get_event_loop()
        await event_loop.sock_sendall(conn, b'OK feeluown 1.0.0\n')
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
            logger.debug('RECV: %s', command)
            cmd = CmdParser.parse(command)
            msg = exec_cmd(app, live_lyric, cmd)
            await event_loop.sock_sendall(conn, bytes(msg, 'utf-8'))

    def run_server(self):
        port = 23333
        host = '0.0.0.0'
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(
            TcpServer(host, port, handle_func=self.handle).run())
        logger.info('Fuo daemon run in {}:{}'.format(host, port))
