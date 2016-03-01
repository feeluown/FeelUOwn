# -*- coding:utf8 -*-

import sys
import asyncio


def init():
    if sys.platform == "darwin":
        from .mac import run
        asyncio.Task(run())
