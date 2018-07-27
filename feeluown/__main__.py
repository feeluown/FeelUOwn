#! /usr/bin/env python3

import asyncio
import logging
import os
import traceback
import sys

sys.path.append(os.path.dirname(sys.path[0]))

from fuocore import MpvPlayer, Library
from fuocore.app import CliMixin
from fuocore.app import run_pubsub, run

from feeluown import logger_config
from feeluown.rcfile import load_rcfile
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR
)
from feeluown.config import config
from feeluown.app import App

logger = logging.getLogger(__name__)


def parse_args(args):
    if '-d' in args:
        config.debug = True
    logger_config()


def ensure_dir():
    if not os.path.exists(HOME_DIR):
        os.mkdir(HOME_DIR)
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    if not os.path.exists(USER_PLUGINS_DIR):
        os.mkdir(USER_PLUGINS_DIR)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    if not os.path.exists(USER_THEMES_DIR):
        os.mkdir(USER_THEMES_DIR)
    if not os.path.exists(SONG_DIR):
        os.mkdir(SONG_DIR)


def excepthook(exc_type, exc_value, tb):
    """Exception hook"""
    src_tb = tb
    while src_tb.tb_next:
        src_tb = src_tb.tb_next
    logger.error('Exception occured: print locals varibales')
    logger.error(src_tb.tb_frame.f_locals)
    traceback.print_exception(exc_type, exc_value, tb)


ensure_dir()
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(PLUGINS_DIR)
sys.path.append(USER_PLUGINS_DIR)


def main():
    sys.excepthook = excepthook
    parse_args(sys.argv)
    player = MpvPlayer()
    player.initialize()
    library = Library()

    if '-nw' not in sys.argv:
        from PyQt5.QtWidgets import QApplication
        from quamash import QEventLoop
        from feeluown.guiapp import GuiMixin

        q_app = QApplication(sys.argv)
        q_app.setQuitOnLastWindowClosed(True)
        q_app.setApplicationName('FeelUOwn')

        app_event_loop = QEventLoop(q_app)
        asyncio.set_event_loop(app_event_loop)
        pubsub_gateway, pubsub_server = run_pubsub()

        class _App(App, CliMixin, GuiMixin):
            mode = App.CLIMode | App.GUIMode

            def __init__(self, player, library, pubsub_gateway):
                App.__init__(self, player, library)
                CliMixin.__init__(self, pubsub_gateway)
                GuiMixin.__init__(self)

        app = _App(player, library, pubsub_gateway)
        load_rcfile(app)
        app.show()
    else:
        pubsub_gateway, pubsub_server = run_pubsub()

        class _App(App, CliMixin):
            mode = App.CLIMode

            def __init__(self, player, library, pubsub_gateway):
                App.__init__(self, player, library)
                CliMixin.__init__(self, pubsub_gateway)

        app = _App(player, library, pubsub_gateway)

    live_lyric = app._live_lyric
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(run(app, live_lyric))
    try:
        event_loop.run_forever()
        logger.info('Event loop stopped.')
    except KeyboardInterrupt:
        # NOTE: gracefully shutdown?
        pass
    finally:
        pubsub_server.close()
        event_loop.close()


if __name__ == '__main__':
    main()
