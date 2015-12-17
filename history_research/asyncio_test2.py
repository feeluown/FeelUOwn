#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import requests
from threading import current_thread


@asyncio.coroutine
def test():
    global loop
    print (current_thread())
    print('before request')
    future = loop.run_in_executor(None, requests.get, 'https://www.baidu.com')
    res = yield from future
    print('after yield request response')
    return res.status_code


@asyncio.coroutine
def run():
    loop.create_task(print_('task'))
    a = yield from test()
    print (a)


@asyncio.coroutine
def print_(text):
    print (current_thread())
    print(text)


global loop
loop = asyncio.get_event_loop()
loop.create_task(run())
print_('first')
loop.run_forever()
