#! /usr/bin/env python3
# -*- coding:utf8 -*-


import sys
import os
import asyncio

path = sys.path[0]
os.chdir(os.path.abspath(path))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from constants import QSS_PATH, LOGFILE, CACHE_PATH, DATA_PATH,\
    MODE, DEBUG, WINDOW_ICON, FEELUOWN_PATH, SONGS_PATH

from controllers import Controller
from quamash import QEventLoop


def ensure_data_dir():
    if not os.path.exists(FEELUOWN_PATH):
        os.mkdir(FEELUOWN_PATH)
    if not os.path.exists(CACHE_PATH):
        os.mkdir(CACHE_PATH)
    if not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)
    if not os.path.exists(SONGS_PATH):
        os.mkdir(SONGS_PATH)


if __name__ == "__main__":
    ensure_data_dir()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setWindowIcon(QIcon(WINDOW_ICON))
    app.setApplicationName("FeelUOwn")
    app_event_loop = QEventLoop(app)
    asyncio.set_event_loop(app_event_loop)

    qss = QSS_PATH
    with open(qss, "r") as qssfile:
        app.setStyleSheet(qssfile.read())

    if MODE != DEBUG:
        f_handler = open(LOGFILE, 'w')
        sys.stdout = f_handler
        sys.stderr = f_handler

    w = Controller()
    w.move(QApplication.primaryScreen().geometry().center() - w.rect().center());
    w.show()

    app_event_loop.run_forever()

    sys.exit()
