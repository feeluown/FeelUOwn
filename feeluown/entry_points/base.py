import logging
import os
import sys
import warnings

from feeluown import logger_config
from feeluown.app import App
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR, COLLECTIONS_DIR
)

logger = logging.getLogger(__name__)


def ensure_dirs():
    for d in (HOME_DIR,
              DATA_DIR,
              USER_THEMES_DIR,
              USER_PLUGINS_DIR,
              CACHE_DIR,
              SONG_DIR,
              COLLECTIONS_DIR):
        if not os.path.exists(d):
            os.mkdir(d)


def setup_config(args, config):
    config.DEBUG = args.debug or config.DEBUG
    config.VERBOSE = args.verbose or config.VERBOSE
    config.MPV_AUDIO_DEVICE = args.mpv_audio_device or config.MPV_AUDIO_DEVICE
    config.LOG_TO_FILE = bool(args.log_to_file or config.LOG_TO_FILE or
                              os.getenv('FUO_LOG_TO_FILE'))

    if args.cmd is not None:
        config.MODE = App.CliMode
        # Always log to file in cli mode because logs may pollute the output.
        config.LOG_TO_FILE = True
    else:
        if not args.no_window:
            try:
                import PyQt5  # noqa, pylint: disable=unused-import
            except ImportError:
                logger.warning('PyQt5 is not installed, fallback to daemon mode.')
            else:
                try:
                    from feeluown.utils.compat import QEventLoop  # noqa
                except ImportError:
                    logger.warning('no QEventLoop, fallback to daemon mode.')
                else:
                    config.MODE |= App.GuiMode
        if not args.no_server:
            config.MODE |= App.DaemonMode


def setup_logger(config):
    if config.DEBUG:
        verbose = 3
    else:
        verbose = config.VERBOSE
    logger_config(verbose=verbose, to_file=config.LOG_TO_FILE)
    # Show deprecation warning when user does not set it.
    if not sys.warnoptions and verbose >= 2:
        warnings.simplefilter('default', DeprecationWarning)
