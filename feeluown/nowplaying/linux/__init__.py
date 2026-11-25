import logging

logger = logging.getLogger(__name__)


def _set_default_dbus_mainloop():
    """Hook dbus-python into the running Qt event loop.

    There are two adapters:

    - GLib (`dbus.mainloop.glib`): the default path. It ships with
      dbus-python, so every install has it, including pip/pipx. It works
      because Qt on Linux runs its event loop on top of GLib's default
      main context (unless QT_NO_GLIB is set).
    - Qt (`dbus.mainloop.pyqt6`): optional. It is not in PyQt6 wheels and
      usually comes from distro packages (e.g. python3-dbus.mainloop.pyqt6).
      It talks to Qt's event loop directly, so it works regardless of
      QT_NO_GLIB. Use it when it is installed.

    The order matters: the GLib adapter never fails at import time, it just
    silently stops dispatching without GLib, so it can't be the one tried first.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from dbus.mainloop.pyqt6 import DBusQtMainLoop
    except ImportError:
        # The default path for most installs, not a degraded mode.
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)
        logger.debug('mpris2 server uses dbus.mainloop.glib')
    else:
        DBusQtMainLoop(set_as_default=True)
        logger.debug('mpris2 server uses dbus.mainloop.pyqt6')


def run_mpris2_server(app):
    # pylint: disable=import-outside-toplevel
    try:
        import dbus
        import dbus.service
    except ImportError as e:
        logger.error("can't run mpris2 server: %s",  str(e))
    else:
        from .mpris2 import Mpris2Service, BusName

        # check if a mainloop was already set
        mainloop = dbus.get_default_main_loop()
        if mainloop is not None:
            logger.warning("mpris2 service already enabled? "
                           "maybe you should remove feeluown-mpris2-plugin")
            return

        # set the mainloop before any dbus operation
        _set_default_dbus_mainloop()
        session_bus = dbus.SessionBus()
        bus = dbus.service.BusName(BusName, session_bus)
        service = Mpris2Service(app, bus)
        service.enable()
