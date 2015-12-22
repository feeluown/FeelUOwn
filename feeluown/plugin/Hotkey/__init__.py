# -*- coding:utf8 -*-

import sys
import asyncio
from _thread import start_new_thread

from controller_api import ControllerApi


def init():
    if sys.platform == "darwin":
        from .mac import run
        asyncio.Task(run())
    elif sys.platform.lower() == "linux":
        from .linux import KeyEventLoop
        event = KeyEventLoop(ControllerApi.player)
        start_new_thread(event.run, ())
