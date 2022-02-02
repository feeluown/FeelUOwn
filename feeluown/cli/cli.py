import asyncio
import os
import sys
from contextlib import contextmanager
from socket import socket, AF_INET, SOCK_STREAM

from feeluown.consts import CACHE_DIR
from feeluown.argparse import add_cmd_parser
from feeluown.library import fmt_artists_names
from feeluown.server.rpc import Request, Response
from feeluown.server.rpc.server import handle_request
from feeluown.utils import aio


OUTPUT_CACHE_FILEPATH = os.path.join(CACHE_DIR, 'cli.out')


def print_error(*args, **kwargs):
    print('\033[0;31m', end='')
    print(*args, **kwargs)
    print('\033[0m', end='')


def init_args_parser(parser):
    add_cmd_parser(parser)


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


def oncemain(app):

    client = OnceClient(app)
    dispatch(app.args, client)

    if app.args.cmd == 'play':

        def on_metadata_changed(metadata):
            if not metadata:
                return
            uri = metadata.get('uri', '')
            text = metadata.get('title', '')
            artists = metadata.get('artists', [])
            if artists:
                text += fmt_artists_names(artists)
            if uri:
                if text:
                    print(f'Playing: {uri} # {text}')
                else:
                    print(f'Playing: {uri}')
            else:
                print(f'Playing: {text}')

        def cb(future):
            try:
                future.result()
            except asyncio.CancelledError:
                # When the coroutine is requested to cancel, stop the player
                # to cancel the task in thread pool.
                app.player.stop()
                app.player.shutdown()
            else:
                app.exit()

        app.player.metadata_changed.connect(on_metadata_changed, weak=False)
        # mpv wait_for_playback will wait until one song is finished,
        # if we have multiple song to play, this will not work well.
        # pylint: disable=protected-access
        future = aio.run_fn(app.player._mpv.wait_for_playback)
        future.add_done_callback(cb)
    else:
        app.exit()
