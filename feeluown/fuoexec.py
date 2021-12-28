"""
exec code with feeluown context
"""
import logging
import os
from functools import wraps
from collections import defaultdict
from math import sin
from typing import Callable

from feeluown.utils.dispatch import Signal
from .consts import DEFAULT_RCFILE_PATH

logger = logging.getLogger(__name__)

_exec_globals = {}


def fuoexec_S(func):
    """function to symbol"""
    return func.__name__


def fuoexec_F(symbol):
    """symbol to function"""
    try:
        return _exec_globals[symbol]
    except KeyError:
        raise RuntimeError('no such symbol in globals')


def fuoexec_load_rcfile(config):
    _exec_globals['config'] = config
    if os.path.exists(DEFAULT_RCFILE_PATH):
        source(DEFAULT_RCFILE_PATH)


def fuoexec_init(app):
    signals_slots_mgr.initialize(app)
    _exec_globals['app'] = app


# add fuoexec_before_app_initialized if needed
# add fuoexec_after_app_initialized if needed


def fuoexec(obj):
    # pylint: disable=exec-used
    exec(obj, _exec_globals)


class Signal:
    def __init__(self, app, name):
        self.name = name

        self._app = app
        self._slot_list: list[tuple[Callable, bool]] = []
        self._slot_symbol_list: list[tuple[str, bool]] = []

    def connect_slots(self):
        """Connect all slots.
        """
        # Find signal object first.
        signal = eval(self.name, {'app': self._app})  # pylint: disable=eval-used

        # Connect slot which are not symbol.
        # These slots are connected directly.
        for slot, aioqueue in self._slot_list:
            signal.connect(slot, weak=True, aioqueue=aioqueue)
        self._slot_list.clear()

        # Connect slots which are symbol currently.
        signal.connect(self.slot_symbols_delegate, weak=False)

    def slot_symbols_delegate(self, *args):
        """
        A delegate invoke the slots for the signal.

        Signal.emit => self.slot_symbols_delegate => slots
        """
        for slot_symbol, aioqueue in self._slot_symbol_list:
            func = fuoexec_F(slot_symbol)
            # FIXME: Duplicate code. The logic has been implemented in Signal.emit.
            if aioqueue:
                Signal.aioqueue.sync_q.put_nowait((func, args))
            else:
                try:
                    func(*args)
                except:  # noqa, pylint: disable=bare-except
                    logger.exception('error during calling slot:%s')



class SignalsSlotsManager:

    def __init__(self):
        self.initialized = False
        self._app = None

        self.signals: dict[str, SignalSymbol] = {}

    def initialize(self, app):
        """
        Find each signal by signal_symbol and connect slots for them.
        """
        if self.initialized:
            raise RuntimeError('signals slots manager already initialized')

        self._app = app
        for signal_symbol in self._signal_symbol_list:
            signal_symbol.connect_slots()
        self.initialized = True

    def add(self, signal_symbol: str, slot: Callable, aioqueue: bool):
        """Add one slot for the signal.

        :param slot: The function or it's symbol.
        """
        if signal_symbol in self.signals:
            signal_

        self._slot_nonsymbols[signal_symbol].add((slot, aioqueue))
        if self.initialized is False:
            self.connect_for_signal_symbol(signal_symbol)

    def add_symbol(self, signal_symbol: str, slot_symbol: str, aioqueue: bool):
        for pair in self._slot_symbols[signal_symbol]:
            # The slot symbol already exists.
            if pair[0] == slot_symbol:
                self._slot_symbols[signal_symbol].remove(pair)
                # The parameter aioqueue may be different.
                self._slot_symbols[signal_symbol].add((slot_symbol, aioqueue))
                break
        else:
            self._slot_symbols[signal_symbol].add((slot_symbol, aioqueue))
            self.connect_for_signal_symbol(signal_symbol)

    def remove(self, signal_symbol, slot_symbol):
        """Remove one slot for signal.
        """
        self._slot_symbols[signal_symbol].remove(slot_symbol)


signals_slots_mgr = SignalsSlotsManager()


def expose_to_rcfile(aliases=None):  # pylint: disable=unused-argument
    """decorator for exposing function to rcfile namespace with aliases

    :param aliases: list or string
    """
    def deco(func):
        nonlocal aliases
        _exec_globals[fuoexec_S(func)] = func
        aliases = aliases if aliases else []
        aliases = aliases if isinstance(aliases, list) else [aliases]
        for alias in aliases:
            _exec_globals[alias] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return deco


@expose_to_rcfile()
def source(filepath):
    with open(filepath, encoding='UTF-8') as f:
        code = compile(f.read(), filepath, 'exec')
        fuoexec(code)


@expose_to_rcfile(aliases='when')
def add_hook(signal_symbol, func, use_symbol=False, aioqueue=True):
    """add hook on signal

    :param signal_symbol: app.{object}.{signal_name} .
    :param func: Signal receiver.
    :param use_symbol: Whether to connect the signal to the symbol of the receiver.
        If this is true, the real receiver is lazy found by the symbol, and
        the signal connects to a symbol instead of a function object.
        If this is false, problem may occur when the rcfile is reloaded.
        because there the signal connects to two *same* receivers.
    :param aioqueue: This is finally passed to Signal.connect.

    Check Signal.connect method for more details.

    >>> def func(): pass
    >>> add_hook('app.initialized', func)

    .. versionadded:: 3.8
       The *aioqueue* keyword argument.
    """
    if use_symbol:
        signals_slots_mgr.add(signal_symbol, fuoexec_S(func), aioqueue=aioqueue)
    else:
        signals_slots_mgr.add(signal_symbol, func)


@expose_to_rcfile()
def rm_hook(signal_symbol: str, func_symbol: str):
    signals_slots_mgr.remove(signal_symbol, func_symbol)
