import argparse
import os
import textwrap
import sys
from contextlib import contextmanager
from socket import socket, AF_INET, SOCK_STREAM

from fuocore.cmds import interprete
from fuocore.cmds.helpers import show_song
from feeluown.consts import CACHE_DIR


OUTPUT_CACHE_FILEPATH = os.path.join(CACHE_DIR, 'cli.out')


def print_error(*args, **kwargs):
    print('\033[0;31m', end='')
    print(*args, **kwargs)
    print('\033[0m', end='')


def setup_cli_argparse(parser):
    subparsers = parser.add_subparsers(dest='cmd')

    play_parser = subparsers.add_parser(
        'play',
        description=textwrap.dedent('''\
        Example:
            - fuo play fuo://netease/songs/3027393
            - fuo play "in the end"
            - fuo play 稻香-周杰伦
        '''),
        formatter_class=argparse.RawTextHelpFormatter
    )
    show_parser = subparsers.add_parser('show')
    search_parser = subparsers.add_parser('search')

    pause_parser = subparsers.add_parser('pause')
    resume_parser = subparsers.add_parser('resume')
    toggle_parser = subparsers.add_parser('toggle')
    stop_parser = subparsers.add_parser('stop')
    next_parser = subparsers.add_parser('next')
    previous_parser = subparsers.add_parser('previous')
    list_parser = subparsers.add_parser('list')
    clear_parser = subparsers.add_parser('clear')
    remove_parser = subparsers.add_parser('remove')
    add_parser = subparsers.add_parser('add')
    status_parser = subparsers.add_parser('status')
    exec_parser = subparsers.add_parser('exec')

    play_parser.add_argument('uri', help='歌曲 uri')
    show_parser.add_argument('uri', help='显示资源详细信息')
    remove_parser.add_argument('uri', help='从播放列表移除歌曲')
    add_parser.add_argument('uri', help='添加歌曲到播放列表')
    search_parser.add_argument('keyword', help='搜索关键字')
    exec_parser.add_argument('code', nargs='?', help='Python 代码')


cmd_handler_mapping = {}


class Request:
    def __init__(self, cmd, *args, **options):
        self.cmd = cmd
        self.args = args
        self.options = options

    @property
    def raw(self):
        text = self.cmd
        if self.args:
            text += ' '
            text += ' '.join(self.args)
        return text

    def __str__(self):
        return '{} {}'.format(self.cmd, self.args)


class Response:
    def __init__(self, code, content):
        self.code = code
        self.content = content

    @classmethod
    def from_text(cls, text):
        if text.endswith('OK\n'):
            return Response(code='OK', content='\n'.join(text.split('\n')[1:-2]))
        return Response('Oops', content='An error occured in server.')


class Client(object):
    def __init__(self, sock):
        self.sock = sock

    def send(self, req):
        self.recv()  # welcome message
        self.sock.send(bytes(req.raw + '\n', 'utf-8'))
        result = self.recv()
        return Response.from_text(result.decode('utf-8'))

    def recv(self):
        result = b''
        while True:
            b = self.sock.recv(256)
            result += b
            if len(b) < 256:
                break
        return result

    def close(self):
        self.sock.close()


@contextmanager
def connect():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('0.0.0.0', 23333))
    client = Client(sock)
    try:
        yield client
    except RuntimeError as e:
        print(e)
    client.close()


class HandlerMeta(type):
    def __new__(cls, name, bases, attrs):
        klass = type.__new__(cls, name, bases, attrs)
        if 'cmds' in attrs:
            cmds = attrs['cmds']
            if isinstance(cmds, str):
                cmd_handler_mapping[cmds] = klass
            else:
                for cmd in cmds:
                    cmd_handler_mapping[cmd] = klass
        return klass


class BaseHandler(metaclass=HandlerMeta):

    def __init__(self, args):
        self.args = args

        self._req = Request(args.cmd)

    def before_request(self):
        pass

    def get_req(self):
        return self._req

    def process_resp(self, resp):
        if resp.code == 'OK':
            if resp.content:
                print(resp.content)
        else:
            print_error(resp.content)


class SimpleHandler(BaseHandler):

    cmds = (
        'pause', 'resume', 'stop',
        'next', 'previous',
        'toggle', 'clear', 'status',
    )


class OneArgHandler(BaseHandler):
    cmds = ('remove', )

    def before_request(self):
        if self.args.cmd == 'remove':
            self._req.args = (self.args.uri, )


class HandlerWithWriteListCache(BaseHandler):
    cmds = ('list', 'search')

    def before_request(self):
        cmd = self.args.cmd
        if cmd == 'search':
            self._req.args = (self.args.keyword, )

    def process_resp(self, resp):
        if resp.code != 'OK' or not resp.content:
            super().process_resp(resp)
            return
        lines = resp.content.split('\n')
        with open(OUTPUT_CACHE_FILEPATH, 'w') as f:
            padding_width = len(str(len(lines)))
            tpl = '{:%dd} {}' % padding_width
            for index, line in enumerate(lines):
                print(tpl.format(index, line))
                f.write('{}\n'.format(line))


class HandlerWithReadListCache(BaseHandler):
    cmds = ('show', 'play')

    def before_request(self):
        uri = self.args.uri
        try:
            lineno = int(uri)
        except ValueError:
            pass
        else:
            with open(OUTPUT_CACHE_FILEPATH) as f:
                i = 0
                for line in f:
                    if i == lineno:
                        uri = line
                        break
                    i += 1
        self._req.args = (uri, )


class AddHandler(BaseHandler):
    cmds = ('add', )

    def before_request(self):
        furi_list = []
        if self.args.uri is None:
            for line in sys.stdin:
                furi_list.append(line.strip())
        else:
            furi_list = [self.args.uri]
        self._req.args = (','.join(furi_list), )


class ExecHandler(BaseHandler):
    cmds = ('exec', )

    def before_request(self):
        code = self.args.code
        if code is None:
            code = sys.stdin.read()
        self._req.args = ('<<EOF\n{}\nEOF\n\n'.format(code), )


class OnceClient:
    def __init__(self, app):
        self._app = app

    def send(self, req):
        app = self._app
        rv = interprete(req.raw,
                        library=app.library,
                        player=app.player,
                        playlist=app.playlist,
                        live_lyric=app.live_lyric)
        return Response.from_text(rv)


def dispatch(args, client):
    HandlerCls = cmd_handler_mapping[args.cmd]
    handler = HandlerCls(args)
    resp = handler.before_request()
    if resp is None:
        resp = client.send(handler.get_req())
    handler.process_resp(resp)


def climain(args):
    """dispatch request"""
    with connect() as cli:
        dispatch(args, cli)


def oncemain(app, args):
    """
    目前的实现有的碰运气，这里可能有一些潜在的问题，
    以后有需求（或者时间）的时候，可以仔细探索下。

    目前已知的可能存在问题（隐患）的点：

    1. 我们只是创建一个 app 对象，没有运行 asyncio event loop,
    2. 像本地音乐插件，它会启动一个异步的任务来扫描本地歌曲，
       我们在这里也没有等待任务结束，就开始执行之后的流程了。

    另外，理论上，该模式的逻辑理应只应该依赖 fuocore 中的模块，
    目前是严格遵守这个要求的。
    """

    client = OnceClient(app)
    dispatch(args, client)

    if args.cmd == 'play':
        song = app.player.current_song
        if song is not None:
            print('Playing: {}'.format(show_song(song, brief=True)))
        else:
            print('Playing: {}'.format(app.player.current_url))
        try:
            app.player._mpv.wait_for_playback()
        except KeyboardInterrupt:
            app.player.stop()
