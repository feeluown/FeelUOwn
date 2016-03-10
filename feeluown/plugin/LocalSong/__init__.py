# -*- coding: utf-8 -*-

import asyncio
from functools import partial

from feeluown.logger import LOG

from .glue import Glue


def init():
    LOG.info('Local Song plugin init')
    glue = Glue()
    app_event_loop = asyncio.get_event_loop()
    app_event_loop.run_in_executor(
        None, partial(glue.get_songs, '/Users/ysw/Music'))
