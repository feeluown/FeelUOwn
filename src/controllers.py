# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

from api import Api
from base.models import DataModel

from widgets.login_dialog import LoginDialog

from views import UiMainWidget
from base.player import Player
from api import Api, get_url_type


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        # QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()
        self.ui.setup_ui(self)
        self.resize(960, 580)
        self.api = Api()
        self.init()

        self.state = {'is_login': False}

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def init(self):
        self.init_signal_binding()
        self.setAttribute(Qt.WA_MacShowFocusRect, False)

    def init_signal_binding(self):
        self.ui.top_widget.login_btn.clicked.connect(self.pop_login)

    """这部分写一些交互逻辑
    """
    def show_playlist(self):
        pass

    """这部分写 pyqtSlot
    """

    @pyqtSlot()
    def pop_login(self):
        if self.state['is_login'] is False:
            w = LoginDialog(self)
            w.signal_login_sucess.connect(self.on_login_success)
            w.show()

    @pyqtSlot(dict)
    def on_login_success(self, data):
        self.state['is_login'] = True





if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
