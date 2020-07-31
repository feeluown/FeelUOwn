from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, \
    QShortcut


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
        self._old_pos = None
        self._widget = None

        # setup window layout
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.setMouseTracking(True)

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)

    def attach_widget(self, widget):
        """set inner widget"""
        self._widget = widget
        self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.insertWidget(0, self._widget)

    def detach(self):
        self._layout.removeWidget(self._widget)
        self._widget = None

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

    def resizeEvent(self, e):
        super().resizeEvent(e)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QLabel

    app = QApplication([])
    widget = QLabel("hello world!")
    window = ResizableFramelessContainer()
    window.attach_widget(widget)
    window.show()
    app.exec()
