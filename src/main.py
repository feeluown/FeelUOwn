#! /usr/bin/env python3
# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys
import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icons/format.ico'))

    path = sys.path[0]
    os.chdir(path)

    sys.exit(app.exec_())

