# -*- coding: utf-8 -*-

import asyncio
import os
import sys

from PyQt5.QtWidgets import QApplication
from quamash import QEventLoop

from .app import App
from .consts import HOME_DIR, USER_PLUGINS_DIR, PLUGINS_DIR, DATA_DIR,\
    CACHE_DIR
from .config import config
from feeluown import logger_config


sys.path.append(PLUGINS_DIR)
sys.path.append(USER_PLUGINS_DIR)


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


def main():
    parse_args(sys.argv)

    q_app = QApplication(sys.argv)
    q_app.setQuitOnLastWindowClosed(True)
    q_app.setApplicationName('FeelUOwn')

    app_event_loop = QEventLoop(q_app)
    asyncio.set_event_loop(app_event_loop)
    app = App()
    app.show()

    app_event_loop.run_forever()
    sys.exit(0)


main()
