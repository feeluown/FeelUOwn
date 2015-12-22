# -*- coding:utf8 -*-

import platform
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from constants import ICON_PATH

width, height = 200, 290


class MiniWidget(QLabel):
    states = ("normal", "hover")

    set_song_like_signal = pyqtSignal([bool])
    play_last_music_signal = pyqtSignal()
    play_next_music_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self.setPixmap(QPixmap(ICON_PATH + "FeelUOwn.png"))

        self._dislike_pixmap = QPixmap(ICON_PATH + "dislike.png")
        self._like_pixmap = QPixmap(ICON_PATH + "like.png")

        self.is_song_like = False

        self.song_name = None
        self.song_singer = None
        self.btns = []

        self._duration = 0
        self._value = 0
        self._angle = 0
        self._state = self.states[0]    # normal

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

        if self._state == self.states[1]:
            rec = QRectF(pen_width/2, (height-width)+slider_width/2, width-slider_width, width-slider_width)
            painter.setBrush(QColor(20, 20, 20, 150))
            painter.drawEllipse(rec)

            pen.setColor(QColor("white"))
            distance = 80
            rec = QRectF(distance/2, (height-width)+distance/2, width-distance, width-distance)
            text_option = QTextOption()
            font = QFont()
            font.setPixelSize(12)
            painter.setFont(font)
            text_option.setWrapMode(QTextOption.WrapAnywhere)
            text_option.setAlignment(Qt.AlignCenter)
            painter.setPen(pen)

            btn_pixmap_width, btn_pixmap_height = 12, 12
            last_btn_top_left_point = QPoint(width/2-40, height-btn_pixmap_height-slider_width-30)
            next_btn_top_left_point = QPoint(width/2+28, height-btn_pixmap_height-slider_width-30)
            painter.drawPixmap(last_btn_top_left_point, QPixmap(ICON_PATH + "mini_last.png"))
            painter.drawPixmap(next_btn_top_left_point,
                               QPixmap(ICON_PATH + "mini_next.png"))

            if self.song_name and self.song_singer:
                painter.drawText(rec, self.song_name + "\n\n" + self.song_singer, text_option)

                like_pixmap_width, like_pixmap_height = 20, 19
                top_left_point_pixmap = QPoint((width-like_pixmap_width)/2, height-like_pixmap_height-slider_width-10)
                if self.is_song_like:
                    painter.drawPixmap(top_left_point_pixmap, self._like_pixmap)
                else:
                    painter.drawPixmap(top_left_point_pixmap, self._dislike_pixmap)

        if self._duration:
            pen_width = slider_width
            pen.setColor(QColor("#993333"))
            pen.setWidth(slider_width)
            rec = QRectF(pen_width/2, (height-width)+pen_width/2, width-pen_width, width-pen_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            span_angle = -(self._value * 1.0 / self._duration) * 360 * 16
            painter.drawArc(rec, 90*16, span_angle)

    def set_song_name(self, text):
        self.song_name = text

    def set_song_singer(self, text):
        self.song_singer = text

    def mousePressEvent(self, event: QMouseEvent):
        # the size of rect should calculate from the painter event
        like_btn_rect = QRect(90, 255, 20, 19)
        last_btn_rect = QRect(60, 242, 12, 12)
        next_btn_rect = QRect(128, 242, 12, 12)
        if like_btn_rect.contains(event.pos()):
            self.set_song_like_signal.emit(not self.is_song_like)
        elif last_btn_rect.contains(event.pos()):
            self.play_last_music_signal.emit()
        elif next_btn_rect.contains(event.pos()):
            self.play_next_music_signal.emit()
        event.ignore()  # pass the event to the parent

    def enterEvent(self, event: QEvent):
        self._state = self.states[1]
        self.update()

    def leaveEvent(self, event: QEvent):
        self._state = self.states[0]
        self.update()

    def set_duration(self, duration):
        self._duration = duration

    def set_value(self, second):
        self._value = second
        if self.isVisible():
            self.update()

    def _init_setting_part(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover)
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

    close_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._drag_pos = QPoint(0, 0)

        self.container = DesktopMiniContainer(self)
        self.content = self.container.central_widget
        self._layout = QVBoxLayout(self)
        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)

        self._exit_shortcut.activated.connect(self.close)

        operation_system = platform.linux_distribution()[0]
        if platform.system() == "Linux":
            if operation_system.lower() != "deepin" or operation_system.lower() != "ubuntu":
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)

        self.setLayout(self._layout)
        self._layout.addWidget(self.container)

        self._layout.setContentsMargins(0, 0, 0, 0)
        # self.setMask(QRegion(0, 0, self.width(), self.height(), QRegion.Ellipse))
        self.setMask(QBitmap(ICON_PATH + "mask.bmp"))
        self.setMouseTracking(True)

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

    def closeEvent(self, event: QCloseEvent):
        self.close_signal.emit()


if __name__ == "__main__":
    import sys, os
    os.chdir("..")
    app = QApplication(sys.argv)
    with open("themes/default.qss", "r") as qssfile:
        app.setStyleSheet(qssfile.read())
    w = DesktopMiniLayer()
    w.setGeometry(100, 100, width, height)
    w.show()
    app.exec_()
