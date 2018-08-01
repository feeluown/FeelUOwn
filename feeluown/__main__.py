#! /usr/bin/env python3

import asyncio
import logging
import os

import traceback
import sys

from fuocore.app import run_server
from fuocore.pubsub import run as run_pubsub

from feeluown import logger_config
from feeluown.rcfile import load_rcfile
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR
)
from feeluown.config import config

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

    cli_only = '-nw' in sys.argv
    if not cli_only:
        try:
            import PyQt5  # noqa
        except ImportError:
            logger.warning('PyQt5 is not installed，can only use CLI mode.')
            cli_only = True

    if not cli_only:
        from PyQt5.QtWidgets import QApplication
        from quamash import QEventLoop
        from feeluown.guiapp import GuiApp

        q_app = QApplication(sys.argv)
        q_app.setQuitOnLastWindowClosed(True)
        q_app.setApplicationName('FeelUOwn')

        app_event_loop = QEventLoop(q_app)
        asyncio.set_event_loop(app_event_loop)
        pubsub_gateway, pubsub_server = run_pubsub()

        app = GuiApp(pubsub_gateway)
        app.initialize()
        load_rcfile(app)
        # TODO: 调用 show 时，会弹出主界面，但这时界面还没开始绘制
        # 为了让提升启动速度，一些非必须的初始化操作可以在 show 之后进行
        app.show()
    else:
        from feeluown.app import CliApp

        pubsub_gateway, pubsub_server = run_pubsub()
        app = CliApp(pubsub_gateway)
        app.initialize()

    live_lyric = app.live_lyric
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(run_server(app, live_lyric))
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
