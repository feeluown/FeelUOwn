# -*- coding:utf8 -*-


from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.desktop_mini_btn = QPushButton("mini")
        self.desktop_mini_btn.setToolTip("切换到迷你窗口")
        self.desktop_mini_btn.setObjectName("show_desktop_mini")

        self.addPermanentWidget(self.desktop_mini_btn)