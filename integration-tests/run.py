#!/usr/bin/env python3

import json
import socket
import sys
import subprocess
import time
import traceback
from contextlib import contextmanager

from feeluown.cli import Client, Request


@contextmanager
def create_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 23333))
    client = Client(sock)
    try:
        yield client
    finally:
        client.close()


def register_dummy_provider():
    req = Request('exec', heredoc='''
from fuocore.provider import dummy_provider
app.library.register(dummy_provider)
''')
    with create_client() as client:
        client.send(req)


def collect():
    for key in globals():
        if key.startswith('test_'):
            test_method = globals()[key]
            yield test_method


def test_show_providers_with_json_format():
    with create_client() as client:
        resp = client.send(Request('show', 'fuo://',
                                   options={'format': 'json'}))
        providers = json.loads(resp.content)
        for provider in providers:
            if provider['identifier'] == 'dummy':
                break
        else:
            assert False, 'dummy provider should be found'


def run():
    popen = subprocess.Popen(['fuo'])
    time.sleep(5)  # wait for fuo starting
    register_dummy_provider()

    for case in collect():
        print('{}...'.format(case.__name__), end='')
        try:
            case()
        except Exception as e:  # noqa
            print('failed')
            traceback.print_exc()
        else:
            print('ok')

    subprocess.run(['fuo', 'exec', 'app.close()'])
    returncode = popen.wait(timeout=2)
    sys.exit(returncode)


if __name__ == '__main__':
    run()
