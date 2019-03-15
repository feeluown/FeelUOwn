from __future__ import print_function

import os
import sys
from contextlib import contextmanager
from socket import socket, AF_INET, SOCK_STREAM


class Client(object):
    def __init__(self, sock):
        self.sock = sock

    def send(self, cmd):
        return self.sock.send(bytes(cmd, 'utf-8'))

    def recv(self):
        result = b''
        while True:
            b = self.sock.recv(256)
            result += b
            if len(b) < 256:
                break
        return result.decode('utf-8')

    def close(self):
        self.sock.close()


@contextmanager
def connect():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('localhost', 23333))
    client = Client(sock)
    try:
        yield client
    except RuntimeError as e:
        print(e)
    client.close()


SIMPLE_CMD_LIST = (
    'pause', 'resume', 'stop',
    'next', 'previous', 'list',
    'toggle', 'clear', 'status',
)

CMD_ALIASES = {
    'rm': 'remove'
}

ONE_ARGS_CMD_LIST = (
    'remove', 'search', 'play', 'show', 'exec',
)

SUPPORTED_CMD_LIST = SIMPLE_CMD_LIST + ONE_ARGS_CMD_LIST

CACHE_CMD_LIST = (
    'list', 'search',
)

INDEX_SUPPORT_CMD_LIST = (
    'remove', 'add', 'play', 'show',
)

OUTPUT_CACHE_FILEPATH = os.path.join(
    os.path.expanduser('~/.FeelUOwn/cache/cli.out'))


def ruok():
    return '\033[0;31maha?\033[0m'


def print_error(*args, **kwargs):
    print('\033[0;31m', end='')
    print(*args, **kwargs)
    print('\033[0m', end='')


def cmd_add(cli):
    if len(sys.argv) not in (2, 3):
        return ruok()
    elif len(sys.argv) == 2:
        furi_list = []
        for line in sys.stdin:
            furi_list.append(line.strip())
    else:
        furi_list = [sys.argv[2]]

    cli.send('add {}\n'.format(','.join(furi_list)))
    rv = cli.recv()
    return rv


def cmd_exec(cli):
    if len(sys.argv) not in (2, 3):
        return ruok()
    if len(sys.argv) == 2:
        text = sys.stdin.read()
    else:
        text = sys.argv[2]

    cli.send('exec <<EOF\n{}\nEOF\n\n'.format(text))
    rv = cli.recv()
    return rv


def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    ensure_path(os.path.dirname(OUTPUT_CACHE_FILEPATH))

    args_length = len(sys.argv)
    if args_length == 1:
        print(ruok())
        print('Supported commands::\n')
        for cmd in SIMPLE_CMD_LIST:
            print('\t', cmd)
        for cmd in ONE_ARGS_CMD_LIST:
            print('\t', cmd, '<xxx>')
        return

    cmd = sys.argv[1]
    with connect() as cli:
        cli.recv()  # receive welcome message
        if cmd in CMD_ALIASES:
            cmd = CMD_ALIASES[cmd]

        if cmd in SIMPLE_CMD_LIST:
            cli.send('{}\n'.format(cmd))
            rv = cli.recv()
        elif cmd == 'add':
            rv = cmd_add(cli)
        elif cmd == 'exec':
            rv = cmd_exec(cli)
        elif cmd in ONE_ARGS_CMD_LIST:
            try:
                arg = sys.argv[2]
            except IndexError:
                print('Not enough args.')
                return
            if cmd in INDEX_SUPPORT_CMD_LIST:
                try:
                    index = int(arg)
                except ValueError:
                    pass
                else:
                    with open(OUTPUT_CACHE_FILEPATH) as f:
                        i = 0
                        for line in f:
                            if i == index:
                                arg = line
                                break
                            i += 1
                        else:
                            print_error('Invalid index.')
                            return
            cli.send('{} {}\n'.format(cmd, arg))
            rv = cli.recv()
        else:
            print_error('Command not found in fuocli.')
            return

    # parse response
    if rv.endswith('OK\n'):
        lines = rv.split('\n')[1:-2]
        if cmd in CACHE_CMD_LIST:
            with open(OUTPUT_CACHE_FILEPATH, 'w') as f:
                padding_width = len(str(len(lines)))
                tpl = '{:%dd} {}' % padding_width
                for index, line in enumerate(lines):
                    print(tpl.format(index, line))
                    f.write('{}\n'.format(line))
        else:
            print('\n'.join(lines))
    elif rv.endswith('Oops\n'):
        print_error('An error occured in server.')
    else:
        print_error('Unknown server error.')


if __name__ == '__main__':
    main()
