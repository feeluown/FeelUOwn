# -*- coding: utf-8 -*-

import janus
import logging
import weakref


logger = logging.getLogger(__name__)


def gen_id(target):
    if hasattr(target, '__func__'):
        return (id(target.__self__), id(target.__func__))
    return id(target)


class Signal:
    """provider signal/slot design pattern

    similar as pyqt signal/slot

    参考 django dispatcher 模块实现
    """
    aioqueue = None
    has_aio_support = False
    worker_task = None

    def __init__(self, name='', *sig):
        self.sig = sig
        self.aioqueued_receiver_ids = set()
        self.receivers = set()

    @classmethod
    def setup_aio_support(cls, loop=None):
        """有些回调函数（比如 Qt UI 操作）只能在主线程中执行，
        我们这里通过 asyncio Queue 来实现。

        这个和 qt signal 的设计类似。
        """
        import asyncio
        loop = asyncio.get_running_loop()
        cls.aioqueue = janus.Queue()
        cls.worker_task = loop.create_task(Signal.worker())
        cls.has_aio_support = True

    @classmethod
    def teardown_aio_support(cls):
        """
        HELP: maybe add a wait_aio_support_teardown method?
        """
        cls.aioqueue.close()
        cls.worker_task.cancel()
        cls.has_aio_support = False
        cls.aioqueue = None

    @classmethod
    async def worker(cls):
        while True:
            func, args = await cls.aioqueue.async_q.get()
            try:
                func(*args)
            except:  # noqa
                logger.exception(f'run {func} with {args} failed')
            cls.aioqueue.async_q.task_done()

    def emit(self, *args):
        # allow remove receiver during emitting
        for receiver in self.receivers.copy():
            try:
                if self._is_alive(receiver):
                    if isinstance(receiver, weakref.ReferenceType):
                        func = receiver()
                    else:
                        func = receiver
                    uid = gen_id(func)
                    aioqueue = uid in self.aioqueued_receiver_ids
                    if aioqueue:
                        if Signal.has_aio_support:
                            Signal.aioqueue.sync_q.put_nowait((func, args))
                        else:
                            raise RuntimeError('Signal has no asyncio support.')
                    else:
                        func(*args)
                else:
                    logger.debug('receiver:{} is dead'.format(receiver))
            except Exception:
                logger.exception('receiver %s raise error' % receiver)

    def _ref(self, receiver):
        ref = weakref.ref
        if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
            ref = weakref.WeakMethod
            receiver_object = receiver.__self__
            weakref.finalize(receiver_object, self._clear_dead_receivers)
        return ref(receiver)

    def connect(self, receiver, weak=True, aioqueue=False):
        """Add a receiver to the sender for signal.

        :param receiver: A function or an instance method that receives the signal.
        :param weak: Whether to use weak references to the receiver.
        :param aioqueue: Whether to put the receiver into a asyncio task queue.
            One thing to remember, the receiver is not invoked immediately
            if this is true. Those receivers which must be invoked in the
            main thread can set this to true.
        """
        if weak:
            self.receivers.add(self._ref(receiver))
        else:
            self.receivers.add(receiver)
        if aioqueue:
            self.aioqueued_receiver_ids.add(gen_id(receiver))

    def disconnect(self, receiver):
        if receiver in self.receivers:
            self.receivers.remove(receiver)
        elif self._ref(receiver) in self.receivers:
            self.receivers.remove(self._ref(receiver))
        else:
            return False
        uid = gen_id(receiver)
        if uid in self.aioqueued_receiver_ids:
            self.aioqueued_receiver_ids.remove(uid)
        return False

    def _is_alive(self, r):
        return not (isinstance(r, weakref.ReferenceType) and r() is None)

    def _clear_dead_receivers(self):
        self.receivers = set([r for r in self.receivers if self._is_alive(r)])


def receiver(signal):
    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func)
        else:
            signal.connect(func)
        return func
    return _decorator
