from PyQt5.QtCore import Qt, QRect, QRectF, QTimer
from PyQt5.QtGui import QColor, QTextOption, QPainter
from PyQt5.QtWidgets import QWidget, QSizeGrip, \
    QSizePolicy, QVBoxLayout


class ResizableFramelessContainer(QWidget):
    """A resizable frameless container

    ResizableFramelessContainer can be moved and resized by mouse.
    Call `attach_widget` to attach an inner widget and `detach` to
    detach the inner widget.

    NOTE: this is mainly designed for picture in picture mode currently.
    """
    def __init__(self,):
        super().__init__(parent=None)

        self._widget = None
        self._timer = QTimer(self)
        self._old_pos = None
        self._widget = None
        self._size_grip = QSizeGrip(self)
        self._timer.timeout.connect(self.__on_timeout)

        # setup window layout
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self._size_grip.setFixedSize(20, 20)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignBottom | Qt.AlignRight)

        self.setMouseTracking(True)

    def attach_widget(self, widget):
        """set inner widget"""
        self._widget = widget
        self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.insertWidget(0, self._widget)

    def detach(self):
        self._layout.removeWidget(self._widget)
        self._widget = None

    def paintEvent(self, e):
        painter = QPainter(self)
        if self._size_grip.isVisible():
            painter.save()
            painter.setPen(QColor('white'))
            option = QTextOption()
            option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            rect = QRect(self._size_grip.pos(), self._size_grip.size())
            painter.drawText(QRectF(rect), '●', option)
            painter.restore()

    def mousePressEvent(self, e):
        self._old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._old_pos is not None:
            delta = e.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = e.globalPos()

    def mouseReleaseEvent(self, e):
        self._old_pos = None

    def enterEvent(self, e):
        super().enterEvent(e)
        if not self._size_grip.isVisible():
            self.resize(self.width(), self.height() + 20)
            self._size_grip.show()
        self._timer.stop()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._timer.start(2000)

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def __on_timeout(self):
        if self._size_grip.isVisible():
            self._size_grip.hide()
            self.resize(self.width(), self.height() - 20)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QLabel

    app = QApplication([])
    widget = QLabel("hello world!")
    window = ResizableFramelessContainer()
    window.attach_widget(widget)
    window.show()
    app.exec()
