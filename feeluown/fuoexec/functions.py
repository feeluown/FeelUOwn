"""
This module contains all functions that exposed to rcfile.
"""

from typing import Callable

from .signal_manager import signal_mgr
from .fuoexec import (
    fuoexec_load_file,
    expose_to_rcfile,
)


# add fuoexec_before_app_initialized if needed
# add fuoexec_after_app_initialized if needed


@expose_to_rcfile()
def source(filepath: str):
    """Exec a py file.
    """
    fuoexec_load_file(filepath)


@expose_to_rcfile(aliases='when')
def add_hook(signal_symbol: str, func: Callable, use_symbol: bool = False, **kwargs):
    """add hook on signal

    :param signal_symbol: app.{object}.{signal_name} .
    :param func: Signal receiver.
    :param use_symbol: Whether to connect the signal to the symbol of the receiver.
        If this is true, the real receiver is lazy found by the symbol, and
        the signal connects to a symbol instead of a function object.
        If this is false, problem may occur when the rcfile is reloaded.
        because there the signal connects to two *same* receivers.
    :param kwargs: This is directly passed to Signal.connect.

    >>> def func(): pass
    >>> add_hook('app.initialized', func)

    .. versionadded:: 3.8
       The *kwargs* keyword argument.
    """
    signal_mgr.add(signal_symbol, func, use_symbol, **kwargs)


@expose_to_rcfile()
def rm_hook(signal_symbol: str, slot: Callable, use_symbol: bool = False):
    """Remove slot from signal.

    If slot_symbol is not connected, this does nothing.
    """
    signal_mgr.remove(signal_symbol, slot, use_symbol=use_symbol)
