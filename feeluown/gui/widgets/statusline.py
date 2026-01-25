from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QTextOption, QColor, QPalette, QPainter

from feeluown.gui.helpers import SOLARIZED_COLORS


class StatusLineItem:
    """Status bar component"""

    def __init__(self, name, widget):
        self.name = name
        self.widget = widget

    def __eq__(self, other):
        return (
            isinstance(other, StatusLineItem)
            and other.name == self.name
            and other.widget is self.widget
        )


class StatuslineLabel(QLabel):
    """
    This is a base class;
    the specific design hasn’t been fully figured out yet,
    and it’s not recommended for widespread use.

    The general idea is as follows: the Label consists of two parts, the middle and
    the notification parts (see Chrome’s extension icon for reference).
    The base class will define the sizes of these two parts and provide some
    predefined drawing functions for subclasses to use.
    """

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app

        # TODO: The height of the forward and back buttons in the top navigation bar
        # is also 30, and it should be passed in externally later
        self._width = self._height = 30
        self._inner_width = self._inner_height = 18
        self._status_width = self._status_height = 13
        self._status_font_size = 8
        self._status_color = "red"
        self._pressed = False

        self.setFixedSize(self._width, self._height)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self._pressed = True
        self.update()

    def mouseReleaseEvent(self, e):
        super().mousePressEvent(e)
        self._pressed = False
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.drawBg(painter)

        painter.save()
        x_delta = (self._width - self._inner_height) // 2
        y_delta = (self._height - self._inner_height) // 2
        painter.translate(x_delta, y_delta)
        self.drawInner(painter)
        painter.restore()

        self.drawStatus(painter)

    def drawInner(self, painter):
        pass

    def drawBg(self, painter):
        if not self._pressed:
            return
        radius = self._width // 2
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._app.theme_mgr.get_pressed_color()))
        painter.drawRoundedRect(self.rect(), radius, radius)
        painter.restore()

    def drawStatus(self, painter):
        if not self.text():
            return

        painter.save()
        font = self.font()
        font.setPixelSize(self._status_font_size)
        painter.setFont(font)
        pen = painter.pen()
        border_color = self.palette().color(QPalette.ColorRole.Window)
        pen.setColor(QColor(border_color))
        painter.setPen(pen)
        w = h = self._width // 2 - 2
        painter.translate(self._width - w, self._width - h)
        text_rect = QRectF(0, 0, w, h)
        text_bg_color = QColor(SOLARIZED_COLORS[self._status_color])
        text_bg_color.setAlpha(225)
        painter.setBrush(text_bg_color)
        radius = 4
        painter.drawRoundedRect(text_rect, radius, radius)
        painter.drawText(
            text_rect, self.text(), QTextOption(Qt.AlignmentFlag.AlignCenter)
        )
        painter.restore()


class StatusLine(QWidget):
    """Status bar (similar to Emacs/Vim status line)"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._items = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

    def get_item(self, name):
        for item in self._items:
            if item.name == name:
                return item

    def add_item(self, item):
        """Add component"""
        if item not in self._items:
            self._items.append(item)
            self._layout.addWidget(item.widget)

    def remove_item(self, item):
        """Remove component

        :param item: A StatusLineItem object, or an item name
        """
        pass
