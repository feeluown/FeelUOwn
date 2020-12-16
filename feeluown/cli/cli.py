import argparse
import asyncio
import os
import textwrap
import sys
from contextlib import contextmanager
from socket import socket, AF_INET, SOCK_STREAM

from feeluown.consts import CACHE_DIR
from feeluown.rpc.cmds.helpers import show_song
from feeluown.rpc import Request, Response
from feeluown.rpc.server import handle_request


OUTPUT_CACHE_FILEPATH = os.path.join(CACHE_DIR, 'cli.out')


def print_error(*args, **kwargs):
    print('\033[0;31m', end='')
    print(*args, **kwargs)
    print('\033[0m', end='')


def setup_cli_argparse(parser):
    subparsers = parser.add_subparsers(dest='cmd')

    # generate icon
    subparsers.add_parser('genicon',
                          description='generate desktop icon')

    fmt_parser = argparse.ArgumentParser(add_help=False)
    fmt_parser.add_argument(
        '--format',
        help="change command output format (default: plain)"
    )

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
    show_parser = subparsers.add_parser('show', parents=[fmt_parser])
    search_parser = subparsers.add_parser(
        'search',
        description=textwrap.dedent('''\
        Example:
            - fuo search hero
            - fuo search 李宗盛 source=xiami,type=artist
            - fuo search 李宗盛 [source=xiami,type=artist]
            - fuo search lizongsheng "source='xiami,qq',type=artist"
            - fuo search 李宗盛 "[source='xiami,qq',type=artist]"
        '''),
        formatter_class=argparse.RawTextHelpFormatter,
        parents=[fmt_parser],
    )

    subparsers.add_parser('pause')
    subparsers.add_parser('resume')
    subparsers.add_parser('toggle')
    subparsers.add_parser('stop')
    subparsers.add_parser('next')
    subparsers.add_parser('previous')
    subparsers.add_parser('list', parents=[fmt_parser])
    subparsers.add_parser('clear')
    subparsers.add_parser('status', parents=[fmt_parser])
    remove_parser = subparsers.add_parser('remove')
    add_parser = subparsers.add_parser('add')
    exec_parser = subparsers.add_parser('exec')

    play_parser.add_argument('uri', help='歌曲 uri')
    show_parser.add_argument('uri', help='显示资源详细信息')
    remove_parser.add_argument('uri', help='从播放列表移除歌曲')
    add_parser.add_argument('uri', nargs='?', help='添加歌曲到播放列表')
    search_parser.add_argument('keyword', help='搜索关键字')
    search_parser.add_argument('options', nargs='?', help='命令选项 (e.g., type=playlist)')
    """
    FIXME: maybe we should redesign options argument or add another way
           to make following examples works

    1. search zjl source='artist,album'

    if quote in options str, bash will remove it, the string
    Python reads will become::

      search zjl source=artist,album

    though user can write this: search zjl source=\'artist,album\'.
    """
    exec_parser.add_argument('code', nargs='?', help='Python 代码')


cmd_handler_mapping = {}


class Client(object):
    def __init__(self, sock):
        self.sock = sock

    def send(self, req):
        rfile = self.sock.makefile('rb')
        rfile.readline()  # welcome message
        self.sock.send(bytes(req.raw + '\n', 'utf-8'))
        line = rfile.readline().decode('utf-8').strip()
        _, code, length = line.split(' ')
        buf = bytearray()
        while len(buf) < int(length) + 2:
            buf.extend(rfile.readline())
        text = bytes(buf[:-2]).decode('utf-8')
        return Response(ok=code.lower() == 'ok', text=text)

    def close(self):
        self.sock.close()


@contextmanager
def connect():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('127.0.0.1', 23333))
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

        options_list = ["format"]
        args_dict = vars(args)
        req_options = {option: args_dict.get(option) for option in options_list
                       if args_dict.get(option, None)}
        self._req = Request(args.cmd, options=req_options)

    def before_request(self):
        """before request hook"""

    def get_req(self):
        return self._req

    def process_resp(self, resp):
        if resp.code == 'OK':
            if resp.text:
                print(resp.text)
        else:
            print_error(resp.text)


class SimpleHandler(BaseHandler):

    cmds = (
        'pause', 'resume', 'stop',
        'next', 'previous',
        'toggle', 'clear', 'status',
    )


class HandlerWithWriteListCache(BaseHandler):
    cmds = ('list', 'search')

    def before_request(self):
        cmd = self.args.cmd
        if cmd == 'search':
            self._req.cmd_args = (self.args.keyword, )
            options_str = self.args.options or ''
            if options_str:
                option_kv_list = options_str.split(',')
            else:
                option_kv_list = []
            for option_kv in option_kv_list:
                k, v = option_kv.split('=')
                self._req.cmd_options[k] = v

    def process_resp(self, resp):
        if resp.code != 'OK' or not resp.text:
            super().process_resp(resp)
            return
        format = self._req.options.get('format', 'plain')
        if format != 'plain':
            print(resp.text)
            return
        lines = resp.text.split('\n')
        with open(OUTPUT_CACHE_FILEPATH, 'w') as f:
            padding_width = len(str(len(lines)))
            tpl = '{:%dd} {}' % padding_width
            for index, line in enumerate(lines):
                print(tpl.format(index, line))
                f.write('{}\n'.format(line))


class HandlerWithReadListCache(BaseHandler):
    cmds = ('show', 'play', 'remove')

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
                        uri = line.split('#')[0].strip()
                        break
                    i += 1
        self._req.cmd_args = (uri, )


class AddHandler(BaseHandler):
    cmds = ('add', )

    def before_request(self):
        furi_list = []
        if self.args.uri is None:
            for line in sys.stdin:
                furi_list.append(line.strip())
        else:
            furi_list = [self.args.uri]
        self._req.cmd_args = (' '.join(furi_list), )


class ExecHandler(BaseHandler):
    cmds = ('exec', )

    def before_request(self):
        code = self.args.code
        if code is None:
            body = sys.stdin.read()
            self._req.has_heredoc = True
            self._req.heredoc_word = 'EOF'
            self._req.set_heredoc_body(body)
        else:
            self._req.cmd_args = (code, )


class OnceClient:
    def __init__(self, app):
        self._app = app

    def send(self, req):
        app = self._app
        return handle_request(req, app)


def dispatch(args, client):
    if '"' in (getattr(args, 'cli', '') or '') \
       or '"' in (getattr(args, 'code', '') or '') \
       or '"' in (getattr(args, 'keyword', '') or ''):
        print_error("command args must not contain charactor '\"'")
        return

    HandlerCls = cmd_handler_mapping[args.cmd]
    handler = HandlerCls(args)
    resp = handler.before_request()
    if resp is None:
        resp = client.send(handler.get_req())
    handler.process_resp(resp)


def climain(args):
    """dispatch request"""

    # FIXME: move this code to somewhere else
    if args.cmd == 'genicon':
        from .install import generate_icon
        generate_icon()
        return

    with connect() as cli:
        dispatch(args, cli)


def oncemain(app, args):
    client = OnceClient(app)
    dispatch(args, client)

    if args.cmd == 'play':
        def on_media_changed(media):
            song = app.player.current_song
            if song is not None:
                print('Playing: {}'.format(show_song(song, brief=True)))
            else:
                print('Playing: {}'.format(app.player.current_media))

        app.player.media_changed.connect(on_media_changed, weak=False)
        loop = asyncio.get_event_loop()
        # mpv wait_for_playback will wait until one song is finished,
        # if we have multiple song to play, this will not work well.
        future = loop.run_in_executor(
            None,
            # pylint: disable=protected-access
            app.player._mpv.wait_for_playback)
        return future
    return None
