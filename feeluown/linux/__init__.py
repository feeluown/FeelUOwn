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
        session_bus = dbus.SessionBus()
        msg = ("mpris2 service already enabled? "
               "maybe you should remove feeluown-mpris2-plugin")
        try:
            # HACK: check if enabled since this will be conflict
            # with feeluown-mpris2-plugin
            bus_names = session_bus._bus_names
        except:  # noqa
            logger.exception("check if mpris2 already enabled failed")
        else:
            if BusName in bus_names:
                logger.warn(msg)
                return

        bus = dbus.service.BusName(BusName, session_bus)
        dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
        try:
            service = Mpris2Service(app, bus)
        except KeyError:
            logger.error(msg)
        else:
            service.enable()
