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

#: sleep is an alias of `asyncio.sleep`.
sleep = asyncio.sleep

#: run is an alias of `asyncio.run`.
run = asyncio.run

#: wait is an alias of `asyncio.wait`.
wait = asyncio.wait

#: gather is an alias of `asyncio.gather`.
gather = asyncio.gather

#: wait_for is an alias of `asyncio.wait_for`
wait_for = asyncio.wait_for

bg_tasks = set()


def run_in_executor(executor, func, *args):
    """alias for loop.run_in_executor"""
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(executor, func, *args)


def run_afn(afn, *args):
    """Alias for create_task

    .. versionadded:: 3.7.8
    """
    return create_task(afn(*args))


def run_afn_ref(afn, *args):
    """Create a background task and keep a reference.

    .. versionadded:: 4.1.9
    """
    task = create_task(afn(*args))
    bg_tasks.add(task)
    task.add_done_callback(bg_tasks.discard)
    return task


def run_fn(fn, *args):
    """Alias for run_in_executor with default executor

    .. versionadded:: 3.7.8
    """
    return run_in_executor(None, fn, *args)
