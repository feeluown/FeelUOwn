# -*- coding: utf-8 -*-

import weakref
import logging

from weakref import WeakMethod


logger = logging.getLogger(__name__)


class Signal(object):
    """provider signal/slot design pattern

    similar as pyqt signal/slot

    参考 django dispatcher 模块实现
    """
    def __init__(self, name='', *sig):
        self.sig = sig
        self.receivers = set()

    def emit(self, *args):
        for receiver in self.receivers:
            try:
                if self._is_alive(receiver):
                    if isinstance(receiver, weakref.ReferenceType):
                        receiver()(*args)
                    else:
                        receiver(*args)
                else:
                    logger.debug('receiver:{} is dead'.format(receiver))
            except Exception as e:
                logger.exception('receiver %s raise error' % receiver)

    def _ref(self, receiver):
        ref = weakref.ref
        if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
            ref = WeakMethod
            receiver_object = receiver.__self__
            weakref.finalize(receiver_object, self._clear_dead_receivers)
        return ref(receiver)

    def connect(self, receiver, weak=True):
        if weak:
            self.receivers.add(self._ref(receiver))
        else:
            self.receivers.add(receiver)

    def disconnect(self, receiver):
        if receiver in self.receivers:
            self.receivers.remove(receiver)
            return True
        ref_receiver = self._ref(receiver)
        if ref_receiver in self.receivers:
            return True
        return False

    def _is_alive(self, r):
        return not(isinstance(r, weakref.ReferenceType) and r() is None)

    def _clear_dead_receivers(self):
        for r in self.receivers:
            if not self._is_alive(r):
                self.receivers.remove(r)


def receiver(signal):
    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func)
        else:
            signal.connect(func)
        return func
    return _decorator
