#! /usr/bin/env python3
# -*- coding:utf8 -*-

from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QShortcut, QVBoxLayout,\
    QFrame, QHBoxLayout, QLabel

from constants import WINDOW_ICON
from base.common import singleton


width, height = 300, 80


@singleton
class NotifyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.sub_widget = _NotifySubWidget(self)
        self.layout.addWidget(self.sub_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._exit_shortcut.activated.connect(self.close)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)

        self.resize(width, height)
        self.move(QApplication.desktop().width() - self.width() - 20, 40)
        self.setLayout(self.layout)

        self._animation = QPropertyAnimation(self, b'windowOpacity')
        self._animation.setStartValue(0.8)
        self._animation.setKeyValueAt(0.4, 1)
        self._animation.setEndValue(0)
        self._animation.setDuration(5000)
        self._animation.finished.connect(self.close)

    def show(self):
        super().show()
        self._animation.start()

    def show_message(self, title, content, pixmap=None):
        if not self.isVisible():
            self.show()
        self._animation.setCurrentTime(0)
        self.sub_widget.set_title(title)
        self.sub_widget.set_content(content)
        pixmap = pixmap if pixmap else QPixmap(WINDOW_ICON)
        self.sub_widget.set_pixmap(pixmap)

    def enterEvent(self, event):
        self._animation.setCurrentTime(0)


class _NotifySubWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            background: #1A2F39;
            border-radius: 10px;
        """)

        self._layout = QHBoxLayout(self)

        self._img_label = QLabel(self)
        self._img_label.setFixedSize(60, 60)
        self._vlayout = QVBoxLayout()
        self._title_label = QLabel(self)
        self._content_label = QLabel(self)
        self._vlayout.addWidget(self._title_label)
        self._vlayout.addWidget(self._content_label)

        self._layout.addWidget(self._img_label)
        self._layout.addSpacing(10)
        self._layout.addLayout(self._vlayout)

        self._init_widget_props()

    def _init_widget_props(self):
        self._title_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #558ACF;
                """)
        self._content_label.setStyleSheet("""
                color: #FBF7E4;
                """)
        self._content_label.setWordWrap(True)

    def set_title(self, title):
        self._title_label.setText(title)

    def set_content(self, content):
        self._content_label.setText(content)

    def set_pixmap(self, pixmap):
        self._img_label.setPixmap(pixmap.scaled(
            self._img_label.size(), transformMode=Qt.SmoothTransformation))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = NotifyWidget()
    w.show()
    w.show_message("Tips", "按ESC可以退出Mini模式哦 按ESC可以退出Mini模式哦")
    sys.exit(app.exec_())
