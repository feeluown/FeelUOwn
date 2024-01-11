#!/usr/bin/env python3

import asyncio
import json
import os
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


def wait_until_23333_service_ok(timeout):
    i = 0
    while i < timeout:
        try:
            with create_client() as client:
                pass
        except ConnectionRefusedError:
            time.sleep(1)
            i += 1
        else:
            return True
    return False


def collect():
    for key in globals():
        if key.startswith('test_'):
            test_method = globals()[key]
            yield test_method


def test_show_providers_with_json_format():
    with create_client() as client:
        resp = asyncio.run(
            client.send(Request('show', ['fuo://'], options={'format': 'json'})))
        json.loads(resp.text)


def test_cmd_options():
    p = subprocess.run(['fuo', 'search', 'xx', '--type=album', '--source=dummy'])
    assert p.returncode == 0


def test_sub_live_lyric():
    for topic in ('topic.live_lyric', 'live_lyric'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 23334))
        sock.settimeout(1)
        welcome = sock.recv(100)
        assert 'pubsub' in welcome.decode('utf-8')
        sock.send(bytes('sub {}\r\n'.format(topic), 'utf-8'))
        response = sock.recv(100)
        assert 'OK' in response.decode('utf-8')
        sock.close()


def run():
    popen = subprocess.Popen(['fuo', '-v'])

    assert wait_until_23333_service_ok(timeout=10)

    failed = False
    for case in collect():
        print('{}...'.format(case.__name__), end='')
        try:
            case()
        except Exception as e:  # noqa
            print('failed')
            traceback.print_exc()
            failed = True
        else:
            print('ok')

    subprocess.run(['fuo', 'exec', 'app.exit()'])
    popen.wait(timeout=10)

    exists = os.path.exists(os.path.expanduser('~/.FeelUOwn/data/state.json'))
    # Since the app may crash during process terminating, the app is considered as
    # existing successfully when the state.json is saved.
    if not exists:
        print('app exits abnormally')
        failed = True

    returncode = 1 if failed is True else 0
    sys.exit(returncode)


if __name__ == '__main__':
    run()
