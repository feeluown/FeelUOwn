# flake8: noqa

import asyncio
from .compat import QEventLoop, QThreadExecutor


def run_in_executor(self, executor, callback, *args):
    """Run callback in executor.

    If no executor is provided, the default executor will be used, which defers execution to
    a background thread.
    """
    # pylint: disable=all

    self._logger.debug('Running callback {} with args {} in executor'.format(callback, args))
    if isinstance(callback, asyncio.Handle):
        assert not args
        assert not isinstance(callback, asyncio.TimerHandle)
        if callback._cancelled:
            f = asyncio.Future()
            f.set_result(None)
            return f
        callback, args = callback.callback, callback.args

    if executor is None:
        self._logger.debug('Using default executor')
        executor = self.get_default_executor()

    if executor is None:
        self._logger.debug('Creating default executor')
        self.set_default_executor_v2(QThreadExecutor())
        executor = self.get_default_executor()

    return asyncio.wrap_future(executor.submit(callback, *args), loop=self)


def get_default_executor(self):
    return getattr(self, 'default_executor', None)


def set_default_executor_v2(self, executor):
    setattr(self, 'default_executor', executor)

    # QEventLoop will shutdown executor when loop is closed
    self.set_default_executor(executor)


def patch_qeventloop():
    # patch note::
    #
    # asyncio.wrap_future should set loop to self, otherwise, we can not call run_in_executor
    # in another thread(the loop not belongs to). The event loop implemented in asyncio
    # library also does this.
    QEventLoop.get_default_executor = get_default_executor
    QEventLoop.set_default_executor_v2 = set_default_executor_v2
    QEventLoop.run_in_executor = run_in_executor


def patch_janus():
    """
    https://github.com/aio-libs/janus/issues/250
    """

    import janus

    janus.current_loop = asyncio.get_event_loop
