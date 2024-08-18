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
        self._use_default_cb = True

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

    def bind_coro(self, coro) -> asyncio.Task:
        """run the coroutine and bind the task

        it will cancel the previous task if exists

        :return: :class:`asyncio.Task`
        """
        self._before_bind()
        if is_in_loop_thread():
            self._task = aio.create_task(coro)
        else:
            self._task = asyncio.run_coroutine_threadsafe(coro, loop=self._mgr.loop)
        if self._use_default_cb:
            self._task.add_done_callback(self._cb)
        return self._task

    def bind_blocking_io(self, func, *args) -> asyncio.Task:
        """run blocking io func in a thread executor, and bind the task

        it will cancel the previous task if exists

        :return: :class:`asyncio.Task`
        """
        self._before_bind()
        self._task = self._mgr.loop.run_in_executor(None, func, *args)
        if self._use_default_cb:
            self._task.add_done_callback(self._cb)
        return self._task

    def disable_default_cb(self):
        self._use_default_cb = False

    def _cb(self, future):
        try:
            future.result()
        except asyncio.CancelledError:
            logger.warning(f'Task {self.name} is cancelled')
        except Exception as e:  # noqa
            logger.exception(f'Task {self.name} failed')


class TaskManager:
    """named task manager

    Usage::

        async def fetch_song():
             pass

        task_name = 'unique-name'

        task_spec = task_mgr.get_or_create(task_name, TaskType.preemptive)
        task = task_spec.bind_coro(fetch_song())
    """
    def __init__(self, *_):
        # only accessible for task instance
        self.loop = asyncio.get_running_loop()

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

    def run_afn_preemptive(self, afn, *args, name=''):
        if not name:
            name = get_fn_name(afn)
        task_spec = self.get_or_create(name)
        return task_spec.bind_coro(afn(*args))

    def run_fn_preemptive(self, fn, *args, name=''):
        if not name:
            name = get_fn_name(fn)
        task_spec = self.get_or_create(name)
        return task_spec.bind_blocking_io(fn, *args)


def get_fn_name(fn):
    if hasattr(fn, '__self__') and hasattr(fn, '__func__'):
        this = fn.__self__
        return f'{this.__module__}.{this.__class__.__name__}.{fn.__name__}'
    return f'{fn.__module__}.{fn.__name__}'
