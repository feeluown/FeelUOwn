import os
import sys
import asyncio


is_travis_env = os.environ.get('TEST_ENV') == 'travis'

cannot_play_audio = is_travis_env

# By set QT_QPA_PLATFORM=offscreen, qt widgets can run on various CI.
cannot_run_qt_test = False
is_macos = sys.platform == 'darwin'


async def aio_waitfor_simple_tasks():
    """
    Many async test cases need to assert some internal tasks must be done,
    but we have no way to confirm if it is done. In most cases, call asyncio.sleep
    to let asyncio schedule the task is enough.

    Here, simple means that the task can be done as long as it is scheduled.

    HELP: find a more robust way to do this.
    """
    await asyncio.sleep(0.001)
