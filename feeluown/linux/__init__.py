import logging

logger = logging.getLogger(__name__)


def run_mpris2_server(app):
    try:
        import dbus
        import dbus.service
        import dbus.mainloop.pyqt5
    except ImportError as e:
        logger.error("can't run mpris2 server: %s",  str(e))
    else:
        from .mpris2 import Mpris2Service, BusName

        # check if a mainloop was already set
        mainloop = dbus.get_default_main_loop()
        if mainloop is not None:
            logger.warn("mpris2 service already enabled? "
                        "maybe you should remove feeluown-mpris2-plugin")
            return

        # set the mainloop before any dbus operation
        dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
        session_bus = dbus.SessionBus()
        bus = dbus.service.BusName(BusName, session_bus)
        service = Mpris2Service(app, bus)
        service.enable()
