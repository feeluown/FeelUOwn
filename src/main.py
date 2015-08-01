#! /usr/bin/env python3
# -*- coding:utf8 -*-


import sys
import os

path = sys.path[0]
os.chdir(path)

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from constants import QSS_PATH, ICON_PATH, LOGFILE, \
    MODE, DEBUG

from controllers import MainWidget
import asyncio
from quamash import QEventLoop, QThreadExecutor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_event_loop = QEventLoop(app)
    asyncio.set_event_loop(app_event_loop)

    qss = QSS_PATH
    with open(qss, "r") as qssfile:
        app.setStyleSheet(qssfile.read())

    if MODE != DEBUG:
        f_handler = open(LOGFILE, 'w')
        sys.stdout = f_handler
        sys.stderr = f_handler

    w = MainWidget()
    w.move((QApplication.desktop().width() - w.width())/2, (QApplication.desktop().height() - w.height())/2)
    w.show()
    # app.exec_()

    with app_event_loop:
        app_event_loop.run_forever()

    sys.exit()


