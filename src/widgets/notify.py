# -*- coding:utf8 -*-

from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QApplication, QShortcut, QVBoxLayout,\
    QFrame


width, height = 300, 80


class NotifyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.widget = _NotifySubWidget(self)
        self.layout.addWidget(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._exit_shortcut.activated.connect(self.close)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(width, height)
        self.move(QApplication.desktop().width() - self.width(), 0)
        self.setLayout(self.layout)

        self._animation = QPropertyAnimation(self, b'windowOpacity')
        self._animation.setStartValue(1)
        self._animation.setEndValue(0)
        self._animation.setDuration(3000)
        self._animation.finished.connect(self.close)

    def show(self):
        super().show()
        self._animation.start()


class _NotifySubWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("background: #222; border-radius: 10px;")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = NotifyWidget()
    w.show()
    sys.exit(app.exec_())
