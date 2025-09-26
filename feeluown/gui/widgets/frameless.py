from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout


class ResizableFramelessContainer(QWidget):
    """A resizable frameless container

    ResizableFramelessContainer can be moved and resized by mouse.
    Call `attach_widget` to attach an inner widget and `detach` to
    detach the inner widget.

    NOTE: this is mainly designed for picture in picture mode currently.
    """

    def __init__(
        self,
    ):
        super().__init__(parent=None)

        self._widget = None
        self._old_pos = None
        self._widget = None

        # setup window layout
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.setMouseTracking(True)

        QShortcut(QKeySequence.StandardKey.Cancel, self).activated.connect(
            self.on_cancel_key_pressed
        )

    def attach_widget(self, widget):
        """set inner widget"""
        self._widget = widget
        self._widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._layout.insertWidget(0, self._widget)

    def detach(self):
        assert self._widget is not None
        self._layout.removeWidget(self._widget)
        self._widget = None

    def mousePressEvent(self, e):
        self._old_pos = e.globalPosition()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.MouseButton.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._old_pos is not None:
            delta = e.globalPosition() - self._old_pos
            self.move(int(self.x() + delta.x()), int(self.y() + delta.y()))
            self._old_pos = e.globalPosition()

    def mouseReleaseEvent(self, e):
        self._old_pos = None

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def on_cancel_key_pressed(self):
        if Qt.WindowState.WindowFullScreen & self.windowState():
            self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen)
        else:
            self.hide()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QLabel

    app = QApplication([])
    widget = QLabel("hello world!")
    window = ResizableFramelessContainer()
    window.attach_widget(widget)
    window.show()
    app.exec()
