# -*- coding: utf-8 -*-

"""feeluown mpris plugin"""

import dbus.mainloop.pyqt5

from feeluown.logger import LOG

from .service import MprisServer


__version__ = '1.0.0'


def init():
    LOG.info("Load mpris plugin")
    dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    MprisServer()
