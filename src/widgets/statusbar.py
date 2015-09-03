# -*- coding:utf8 -*-


from PyQt5.QtWidgets import *
from widgets.playmode_label import PlaymodeSwitchLabel


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.desktop_mini_btn = QPushButton("mini")
        self.playmode_switch_label = PlaymodeSwitchLabel()
        self.desktop_mini_btn.setToolTip("切换到迷你窗口")
        self.desktop_mini_btn.setObjectName("show_desktop_mini")

        self.addPermanentWidget(self.playmode_switch_label)
        self.addPermanentWidget(self.desktop_mini_btn)