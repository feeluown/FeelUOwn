# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class SettingSubWidgetContainer(QWidget):
    def __init__(self, title, widget=None):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.title_label = QLabel(title)

        self.title_label.setStyleSheet("""
            background: transparent;
            color: white;
            padding-left: 2px;
            font-size: 14px;
        """)
        # self.setStyleSheet("background: white;")  # no effect, dont know why

        self._layout.addWidget(self.title_label)
        self._layout.addSpacing(5)
        if widget:
            self._layout.addWidget(widget)
        self.setLayout(self._layout)

    def set_widget(self, widget):
        self._layout.addWidget(widget)


class SettingWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._init_props()
        self._init_layout_props()
        self._init_setting_part()

    def _init_setting_part(self):
        self._layout.addSpacing(10)

        path_edit = FilePathLineEdit()
        local_music_container = SettingSubWidgetContainer("本地音乐", path_edit)
        self._layout.addWidget(local_music_container)

        self._layout.addStretch(1)

    def _init_props(self):
        self.setObjectName("setting_widget")

    def _init_layout_props(self):
        self._layout.setContentsMargins(100, 5, 100, 5)  # left, top, right, bottom


class SettingWidgetContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.central_widget = SettingWidget(self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.central_widget)

        self.setObjectName("setting_widget_container")
        self.setStyleSheet("background: rgba(0, 0, 0, 0.8); border-radius: 8px;")
        self._layout.setContentsMargins(0, 0, 0, 0)


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

        self._layout.setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, event: QCloseEvent):
        self.deleteLater()
        pass


class FilePathLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setObjectName("FilePathLineEdit")

        self.setFixedHeight(28)

        self.setStyleSheet("""
            padding: 0px 10px;
            border-radius: 3px;
            font-size: 12px;
            color: gray;
            background-color: rgba(0, 0, 0, 0.4);
        """)
        self.setText("~/Music/")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    with open("../themes/default.qss", "r") as qssfile:
        app.setStyleSheet(qssfile.read())
    w = SettingWidgetLayer()
    w.setGeometry(100, 100, 600, 360)
    w.show()
    app.exec_()
