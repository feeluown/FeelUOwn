import sys
import logging


logger = logging.getLogger(__name__)


async def run_nowplaying_server(app):
    try:
        run_nowplaying_server_internal(app)
    except ImportError as e:
        logger.warn(f"run nowplaying server failed: '{e}'")


async def run_nowplaying_server_internal(app):
    if sys.platform == 'linux':
        from .linux import run_mpris2_server
        await run_mpris2_server(app)
    elif sys.platform in ('win32', 'darwin'):
        from .nowplaying import NowPlayingService
        if sys.platform == 'darwin':
            from .macos import MacosMixin

            class Service(MacosMixin, NowPlayingService):
                pass
        else:
            Service = NowPlayingService
        service = Service(app)
        await service.start()
    else:
        logger.warn('nowplaying is not supported on %s', sys.platform)
