from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget


class Overlay(QWidget):
    """Base overlay widget that can be shown on top of other widgets.
    
    Features:
    - Semi-transparent background
    - Auto-resizing to parent
    - Click outside to close
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent
        self.setWindowFlags(Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

    def showEvent(self, event):
        """Resize to parent when shown"""
        if self._parent:
            self.resize(self._parent.size())
        super().showEvent(event)

    def paintEvent(self, event):
        """Draw semi-transparent background"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def eventFilter(self, obj, event):
        """Handle parent resize events"""
        if self.isVisible() and obj == self._parent and event.type() == QEvent.Resize:
            self.resize(self._parent.size())
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """Click outside to close"""
        if not self.rect().contains(event.pos()):
            self.hide()
        super().mousePressEvent(event)
