# -*- coding=utf8 -*-
__author__ = 'cosven'

import sys
import os
from PyQt4.QtGui import *
from controllers import MainWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    path = sys.path[0]
    os.chdir(path)
    # float center
    w = MainWidget()
    w.move((QApplication.desktop().width() - w.width())/2,(QApplication.desktop().height() - w.height())/2)
    w.show()
    sys.exit(app.exec_())

