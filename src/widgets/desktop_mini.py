# -*- coding:utf8 -*-

import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


width = height = 160


class CirclePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap=None):
        super().__init__(pixmap)
        if pixmap:
            self._init_rotate_center()

    def setPixmap(self, pixmap: QPixmap):
        super().setPixmap(pixmap)
        self._init_rotate_center()

    def _init_rotate_center(self):
        self.setTransformOriginPoint(self.pixmap().width()/2, self.pixmap().height()/2)


class DesktopScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)


class DesktopView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)

        self.img_ani = QVariantAnimation()

        self._scene = DesktopScene(self)
        self.setScene(self._scene)

        self._scene.setSceneRect(QRectF(QPointF(0, 0), QSizeF(self.size())))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setStyleSheet("background: transparent;")

        self.img_item = CirclePixmapItem()
        self.img_item.setPixmap(QPixmap("desktop.jpg"))

        self._scene.addItem(self.img_item)

        self._init_props()
        self._init_signal_binding()

        self.img_ani.start()

    def _init_props(self):
        self.img_ani.setLoopCount(-1)
        self.img_ani.setDuration(10000)
        self.img_ani.setStartValue(QVariant(0.0))
        self.img_ani.setEndValue(QVariant(360.0))

    def _init_signal_binding(self):
        self.img_ani.valueChanged.connect(self._rotate_img)

    @pyqtSlot(QVariant)
    def _rotate_img(self, angle):
        self.img_item.setRotation(angle)

    @pyqtSlot(QVariant)
    def _show_song_progress(self, ms):
        progress_item = QGraphicsEllipseItem(0, 0, width, height)
        progress_item.setStartAngle(16*ms)
        progress_item.setSpanAngle(16)
        self._scene.addItem(progress_item)

    @pyqtSlot()
    def _on_song_changed(self):
        self._scene.clear()


class DesktopContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._drag_pos = (0, 0)
        self.setFixedSize(width, height)

        self._view = DesktopView(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMask(QRegion(0, 0, width, height, QRegion.Ellipse))

        self._exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._init_signal_binding()

    def _init_signal_binding(self):
        self._exit_shortcut.activated.connect(self.close)

    def paintEvent(self, event: QPaintEvent):
        if sys.platform == "darwin":
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.rect(), Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

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
    import sys
    app = QApplication(sys.argv)
    w = DesktopContainer()
    w.show()
    sys.exit(app.exec_())
