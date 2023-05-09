import sys
import logging


logger = logging.getLogger(__name__)


async def run_nowplaying_server(app):
    try:
        await run_nowplaying_server_internal(app)
    except ImportError as e:
        logger.warning(f"run nowplaying service failed: '{e}'")
    except:  # noqa
        logger.exception('run nowplaying service error')


def get_service_cls():
    """
    Only public for testing.
    """
    # pylint: disable=import-outside-toplevel
    from .nowplaying import NowPlayingService

    if sys.platform == 'darwin':
        from .macos import MacosMixin

        class Service(MacosMixin, NowPlayingService):
            pass
    else:
        Service = NowPlayingService
    return Service


async def run_nowplaying_server_internal(app):
    # pylint: disable=import-outside-toplevel
    if sys.platform == 'linux':
        from .linux import run_mpris2_server
        run_mpris2_server(app)
    elif sys.platform in ('win32', 'darwin'):
        service = get_service_cls()(app)
        await service.start()
    else:
        logger.warning('nowplaying is not supported on %s', sys.platform)
