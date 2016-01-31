# -*- coding:utf8 -*-

import sys
import asyncio
from functools import partial


def init():
    if sys.platform == "darwin":
        from .mac import run
        asyncio.Task(run())
    elif sys.platform.lower() == "linux":
        from .linux import KeyEventLoop
        event = KeyEventLoop()
        app_event_loop = asyncio.get_event_loop()
        app_event_loop.run_in_executor(None, partial(event.run))
