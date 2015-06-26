#! /usr/bin/env python3
# -*- coding:utf8 -*-


import sys
import os

path = sys.path[0]
os.chdir(path)

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from setting import QSS_PATH, ICON_PATH, LOGFILE

from controllers import MainWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss = QSS_PATH
    with open(qss, "r") as qssfile:
        app.setStyleSheet(qssfile.read())

    w = MainWidget()
    w.move((QApplication.desktop().width() - w.width())/2, (QApplication.desktop().height() - w.height())/2)
    w.show()
    app.exec_()

    sys.exit()


