# -*- coding: utf-8 -*-

import weakref
import logging

from weakref import WeakMethod


logger = logging.getLogger(__name__)


class Signal(object):
    """provider signal/slot design pattern

    similar as pyqt signal/slot
    """
    def __init__(self, name='', *sig):
        self.sig = sig
        self.receivers = set()

    def emit(self, *args):
        for receiver in self.receivers:
            try:
                receiver()(*args)
            except Exception:
                logger.exception('receiver %s run error' % receiver())

    def _ref(self, receiver):
        ref = weakref.ref
        if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
            ref = WeakMethod
        return ref(receiver)

    def connect(self, receiver):
        self.receivers.add(self._ref(receiver))

    def disconnect(self, receiver):
        receiver = self._ref(receiver)
        if receiver in self.receivers:
            self.receivers.remove(receiver)
            return True
        return False


def receiver(signal):
    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func)
        else:
            signal.connect(func)
        return func
    return _decorator
