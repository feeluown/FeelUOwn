from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)


DEFAULT_RCFILE_PATH = os.path.expanduser('~/.fuorc')

_registered_signal_slot = defaultdict(list)


def when(signal_name, func):
    """
    :param signal_name: app.{object}.{signal_name}

    >>> def func(): pass
    >>> when('app.initialized', func)
    """
    _registered_signal_slot[signal_name].append(func)


def bind_signals(app):
    for signal_name, slots in _registered_signal_slot.items():
        signal = eval(signal_name)
        for slot in slots:
            signal.connect(slot)


def load_rcfile(config, rcfile_path=DEFAULT_RCFILE_PATH):
    if not os.path.exists(DEFAULT_RCFILE_PATH):
        return

    g = {'when': when, 'config': config}
    with open(rcfile_path, encoding='UTF-8') as f:
        exec(f.read(), g)
