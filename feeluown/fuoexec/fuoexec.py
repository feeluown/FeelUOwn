"""
TODO: remove fuoexec prefix from these functions.
"""

import os
from functools import wraps
from typing import Callable, Any, Dict

from feeluown.config import Config
from feeluown.consts import DEFAULT_RCFILE_PATH


_exec_globals: Dict[str, Any] = {}


def fuoexec_get_globals() -> Dict:
    return _exec_globals


def fuoexec_S(func: Callable) -> str:
    """function to symbol"""
    return func.__name__


def fuoexec_F(symbol: str) -> Callable:
    """symbol to function"""
    try:
        return fuoexec_get_globals()[symbol]
    except KeyError:
        raise RuntimeError('no such symbol in globals') from None


def fuoexec_load_file(filepath: str):
    with open(filepath, encoding='UTF-8') as f:
        code = compile(f.read(), filepath, 'exec')
        fuoexec(code)


def fuoexec_load_rcfile(config: Config):
    fuoexec_get_globals()['config'] = config
    if os.path.exists(DEFAULT_RCFILE_PATH):
        fuoexec_load_file(DEFAULT_RCFILE_PATH)


def fuoexec_init(app):
    from feeluown.library import resolve, reverse

    signal_mgr.initialize(app)
    fuoexec_get_globals()['app'] = app
    fuoexec_get_globals()['resolve'] = resolve
    fuoexec_get_globals()['reverse'] = reverse


def fuoexec(obj):
    # pylint: disable=exec-used
    exec(obj, fuoexec_get_globals())


def expose_to_rcfile(aliases=None) -> Callable:  # pylint: disable=unused-argument
    """Decorator for exposing function to rcfile namespace with aliases

    :param aliases: list or string
    """
    def deco(func):
        nonlocal aliases

        g = fuoexec_get_globals()
        g[fuoexec_S(func)] = func
        aliases = aliases if aliases else []
        aliases = aliases if isinstance(aliases, list) else [aliases]
        for alias in aliases:
            g[alias] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return deco


# pylint: disable=wrong-import-position, cyclic-import
from .signal_manager import signal_mgr  # noqa
