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
        from .mpris2 import Mpris2Service
        dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
        try:
            service = Mpris2Service(app)
        except KeyError:
            logger.warning("mpris2 service already enabled? "
                           "maybe you should remove feeluown-mpris2-plugin")
        else:
            service.enable()
