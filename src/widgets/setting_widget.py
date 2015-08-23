# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class SettingWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_props()
        self.setText("HELLO WORLD")

    def _init_props(self):
        self.setObjectName("setting_widget")


class SettingWidgetContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.central_widget = SettingWidget(self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.central_widget)

        self.setStyleSheet("background: rgba(0, 0, 0, 0.2); border-radius: 20px;")

        self.setObjectName("setting_widget_container")

        # self._blur_effect = QGraphicsBlurEffect(self)
        # self._blur_effect.setBlurRadius(5)
        # self.setGraphicsEffect(self._blur_effect)


class SettingWidgetLayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.container = SettingWidgetContainer(self)
        self._layout = QVBoxLayout(self)
        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)

        self._exit_shortcut.activated.connect(self.close)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setLayout(self._layout)
        self._layout.addWidget(self.container)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = SettingWidgetLayer()
    w.setGeometry(100, 100, 600, 360)
    w.show()
    app.exec_()
