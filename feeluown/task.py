import asyncio
import logging
import threading
from enum import Enum

from feeluown.utils import aio

logger = logging.getLogger(__name__)


def is_in_loop_thread():
    """check if current thread has event loop"""
    return threading.current_thread() is threading.main_thread()


class TaskKind(Enum):
    preemptive = 'preemptive'  #: preemptive task
    cooperative = 'cooperative'  #: cooperative task


class PreemptiveTaskSpec:
    """Preemptive task specification (threadsafe)"""

    def __init__(self, mgr, name):
        """

        :param mgr: :class:`TaskManager`
        :param name: task unique name
        """
        self._mgr = mgr
        self.name = name
        self.kind = TaskKind.preemptive
        self._task = None

    def _before_bind(self):
        if self._task is None:
            return
        if not self._task.done():
            logger.info('preemptive-task(%s): try to cancel previous', self.name)
        if is_in_loop_thread():
            self._task.cancel()
        else:
            self._mgr.loop.call_soon_threadsafe(self._task.cancel)
        self._task = None

    def bind_coro(self, coro):
        """run the coroutine and bind the task

        it will cancel the previous task if exists

        :return: :class:`asyncio.Task`
        """
        self._before_bind()
        if is_in_loop_thread():
            self._task = aio.create_task(coro)
        else:
            self._task = asyncio.run_coroutine_threadsafe(coro, loop=self._mgr.loop)
        return self._task

    def bind_blocking_io(self, func, *args):
        """run blocking io func in a thread executor, and bind the task

        it will cancel the previous task if exists

        :return: :class:`asyncio.Task`
        """
        self._before_bind()
        self._task = self._mgr.loop.run_in_executor(None, func, *args)
        return self._task


class TaskManager:
    """named task manager

    Usage::

        async def fetch_song():
             pass

        task_name = 'unique-name'

        task_spec = task_mgr.get_or_create(task_name, TaskType.preemptive)
        task = task_spec.bind_coro(fetch_song())
    """
    def __init__(self, app, loop):
        """

        :param app: feeluown app instance
        :param loop: asyncio event loop
        """
        self._app = app

        # only accessible for task instance
        self.loop = loop

        # store the name:taskspec mapping
        self._store = {}

    def get_or_create(self, name, kind=TaskKind.preemptive):
        """get task spec, it will be created if not exists

        :param name: task identifier(name)
        :param kind: :class:`TaskKind`

        TODO: client should register first, then get by name
        """
        if name not in self._store:
            task_spec = self._create(name, kind)
        else:
            task_spec = self._store[name]
        return task_spec

    def _create(self, name, kind):
        kind = TaskKind(kind)
        task_spec = PreemptiveTaskSpec(self, name)
        self._store[name] = task_spec
        return task_spec
