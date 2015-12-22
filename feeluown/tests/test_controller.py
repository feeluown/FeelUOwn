# -*- coding:utf8 -*-
import asyncio
from quamash import QEventLoop
from PyQt5.QtWidgets import QApplication

from feeluown.controllers import Controller


def test_controller_start():
    import sys
    app = QApplication(sys.argv)
    app_event_loop = QEventLoop(app)
    asyncio.set_event_loop(app_event_loop)
    w = Controller()
    w.show()
