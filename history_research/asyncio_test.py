#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import requests


def do_request():
    print ('request start')
    res = requests.get('https://api.github.com/repos/cosven/FeelUOwn/releases')
    print ('request stop')


def hei():
    print ('hei start')
    requests.get('https://api.github.com/repos/cosven/memo/releases')
    print ('hei')


def do_dead_loop():
    global loop
    print ('loop start')
    loop.call_soon(do_request)
    requests.get('https://api.github.com/repos/cosven/memo/releases')
    hei()
    print ('loop middle')
    requests.get('https://api.github.com/repos/cosven/memo/releases')
    print ('loop end')



global loop
loop = asyncio.get_event_loop()

loop.call_soon(do_dead_loop)
print('main end')
loop.run_forever()
