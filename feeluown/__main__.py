# -*- coding: utf-8 -*-

import sys
import asyncio

from PyQt5.QtWidgets import QApplication
from quamash import QEventLoop

from .app import App
from .consts import USER_PLUGINS_DIR, PLUGINS_DIR
from .config import config
from feeluown import logger_config


sys.path.append(PLUGINS_DIR)
sys.path.append(USER_PLUGINS_DIR)


def parse_args(args):
    if '-d' in args:
        config.debug = True
    logger_config()


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
