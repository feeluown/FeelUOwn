# -*- coding: utf-8 -*-

"""feeluown mpris plugin"""

from feeluown.logger import LOG
from feeluown.utils import is_linux

__version__ = '1.0.0'


def init():
    if not is_linux():
        return 0
    from .service import MprisServer
    import dbus.mainloop.pyqt5
    LOG.info("Load mpris plugin")
    dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    MprisServer()
