"""
encapsulate asyncio API
~~~~~~~~~~~~~~~~~~~~~~~

Asyncio has added some new API in Python 3.7 and 3.8, e.g.,
gather, run and create_task. They are recommended in newer version.
However, FeelUOwn is supposed to be compatible with Python 3.5,
we will backport some API here. In addition, we create alias
for some frequently used API.
"""

import asyncio
import sys


if sys.version_info >= (3, 7):
    # create_task is temporarily not working properly with quamash
    # https://github.com/harvimt/quamash/issues/116
    create_task = asyncio.ensure_future
else:
    create_task = asyncio.ensure_future

#: alias for create_task
spawn = create_task
as_completed = asyncio.as_completed


def run_in_executor(executor, func, *args):
    """alias for loop.run_in_executor"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, func, *args)
