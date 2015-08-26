# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from constants import ICON_PATH

width, height = 200, 290


class MiniWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self.setPixmap(QPixmap(ICON_PATH + "FeelUOwn.png"))

        self._duration = 0
        self._value = 0
        self._angle = 0

        self._init_props()
        self._init_setting_part()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.HighQualityAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setBrush(QColor("#222"))
        painter.drawRect(0, 0, width, height-width)

        slider_width = 6.0

        painter.resetTransform()
        painter.translate(self.width()/2, self.width()/2 + height-width)
        # painter.rotate(self._angle)
        painter.drawPixmap(-self.width()/2, -self.width()/2, self.pixmap().scaled(width, width))

        painter.resetTransform()
        pen_width = slider_width
        rec = QRectF(pen_width/2, (height-width)+pen_width/2, width-pen_width, width-pen_width)
        pen = QPen()
        pen.setWidth(slider_width)
        pen.setColor(QColor("#CCC"))
        pen.setColor(QColor(200, 200, 200, 80))
        painter.setPen(pen)
        painter.drawArc(rec, 0, 360 * 16)

        # pen_width = 4.0
        # rec = QRectF(pen_width/2, (height-width)+pen_width/2, width-pen_width, width-pen_width)
        # pen.setWidth(pen_width)
        # painter.setPen(pen)
        # painter.drawArc(rec, 0, 360 * 16)

        if self._duration:
            pen_width = slider_width
            pen.setColor(QColor("#993333"))
            pen.setWidth(slider_width)
            rec = QRectF(pen_width/2, (height-width)+pen_width/2, width-pen_width, width-pen_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            span_angle = -(self._value * 1.0 / self._duration) * 360 * 16
            painter.drawArc(rec, 90*16, span_angle)

    def set_duration(self, duration):
        self._duration = duration

    def set_value(self, second):
        self._value = second
        self.update()

    def _init_setting_part(self):
        pass

    def _init_props(self):
        self.setObjectName("setting_widget")


class DesktopMiniContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.central_widget = MiniWidget(self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._layout.addWidget(self.central_widget)

        self.setObjectName("setting_widget_container")
        self.setStyleSheet("background: transparent;")
        self._layout.setContentsMargins(0, 0, 0, 0)


class DesktopMiniLayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._drag_pos = (0, 0)

        self.container = DesktopMiniContainer(self)
        self.content = self.container.central_widget
        self._layout = QVBoxLayout(self)
        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)

        self._exit_shortcut.activated.connect(self.close)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setLayout(self._layout)
        self._layout.addWidget(self.container)

        self._layout.setContentsMargins(0, 0, 0, 0)
        # self.setMask(QRegion(0, 0, self.width(), self.height(), QRegion.Ellipse))
        self.setMask(QBitmap(ICON_PATH + "mask.bmp"))

        self._init_position()

    def _init_position(self):
        self.move(QApplication.desktop().width() - self.width(), 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        if event.buttons() == Qt.RightButton:
            event.ignore()


if __name__ == "__main__":
    import sys, os
    app = QApplication(sys.argv)
    with open("../themes/default.qss", "r") as qssfile:
        app.setStyleSheet(qssfile.read())
    w = DesktopMiniLayer()
    w.setGeometry(100, 100, width, height)
    w.show()
    app.exec_()
