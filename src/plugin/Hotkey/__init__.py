# -*- coding:utf8 -*-

import sys
import asyncio
from _thread import start_new_thread


def init(controller):
    if sys.platform == "darwin":
        from .mac import run_event_loop
        player = controller.player
        APP_EVENT_LOOP = asyncio.get_event_loop()
        APP_EVENT_LOOP.call_later(1, run_event_loop, player)
    elif sys.platform.lower() == "linux":
        from .linux import KeyEventLoop
        event = KeyEventLoop(controller.player)
        start_new_thread(event.run, ())