#! /usr/bin/env python
# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys
import os
from PyQt4.QtGui import *
from controllers import MainWidget, LoginDialog


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icons/format.ico'))
    path = sys.path[0]
    os.chdir(path)

    qss = "themes/default.qss"
    with open(qss, "r") as qssfile:
        app.setStyleSheet(qssfile.read())
    w = MainWidget()
    w.move((QApplication.desktop().width() - w.width())/2,(QApplication.desktop().height() - w.height())/2)
    w.show()
    sys.exit(app.exec_())

