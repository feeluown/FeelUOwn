#! /usr/bin/env python3
# -*- coding:utf8 -*-


import sys
import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from setting import QSS_PATH, ICON_PATH
from base.logger import LOG
from controllers import MainWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    path = sys.path[0]
    os.chdir(path)

    qss = QSS_PATH
    with open(qss, "r") as qssfile:
        app.setStyleSheet(qssfile.read())

    w = MainWidget()
    w.move((QApplication.desktop().width() - w.width())/2, (QApplication.desktop().height() - w.height())/2)
    w.show()
    sys.exit(app.exec_())
