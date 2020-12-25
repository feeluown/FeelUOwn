"""
exec code with feeluown context
"""
import logging
import os
from functools import wraps
from collections import defaultdict

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


class SignalsSlotsManager:

    def __init__(self):
        self.initialized = False
        self._app = None
        self.signal_proxy_map = {}
        self.signal_slots_map = defaultdict(set)

    def initialize(self, app):
        if self.initialized:
            raise RuntimeError('signals slots manager already initialized')

        self._app = app
        for signal_symbol in self.signal_slots_map.keys():
            self._create_signal_proxy(signal_symbol)
        self.initialized = True

    def add(self, signal_symbol, slot):
        """add one slot for signal

        :param string signal: signal symbol
        :param slot: slot name or slot
        """
        if self.initialized and signal_symbol not in self.signal_slots_map:
            self._create_signal_proxy(signal_symbol)
        self.signal_slots_map[signal_symbol].add(slot)

    def remove(self, signal_symbol, slot):
        """remove one slot for signal

        :param slot: string or function
        """
        if slot in self.signal_slots_map[signal_symbol]:
            self.signal_slots_map[signal_symbol].remove(slot)
            if not self.signal_slots_map[signal_symbol]:
                self.signal_proxy_map.pop(signal_symbol)

    def _create_signal_proxy(self, signal_symbol):
        def create(this, signal_symbol):
            def signal_proxy(*args, **kwargs):
                for slot in this.signal_slots_map.get(signal_symbol, []):
                    func = fuoexec_F(slot) if isinstance(slot, str) else slot
                    try:
                        func(*args, **kwargs)
                    except:  # noqa, pylint: disable=bare-except
                        logger.exception('error during calling slot:%s')
            return signal_proxy

        # pylint: disable=eval-used
        signal = eval(signal_symbol, {'app': self._app})
        signal_proxy = create(self, signal_symbol)
        signal.connect(signal_proxy, weak=True, aioqueue=True)
        self.signal_proxy_map[signal] = signal_proxy


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
def add_hook(signal_symbol, func, use_symbol=False):
    """add hook on signal

    :param signal_symbol: app.{object}.{signal_name}
    :param func: signal callback function

    >>> def func(): pass
    >>> add_hook('app.initialized', func)
    """
    if use_symbol:
        signals_slots_mgr.add(signal_symbol, fuoexec_S(func))
    else:
        signals_slots_mgr.add(signal_symbol, func)


@expose_to_rcfile()
def rm_hook(signal_symbol, func_symbol):
    signals_slots_mgr.remove(signal_symbol, func_symbol)
