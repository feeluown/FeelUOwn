from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QBrush, QPixmap, QImage, QColor
from PyQt5.QtWidgets import QWidget


class PixmapDrawer:
    """Draw pixmap on a widget with radius.

    The pixmap will be scaled to the width of the widget.
    """
    def __init__(self, img, widget: QWidget, radius: int = 0):
        """
        :param widget: a object which has width() and height() method.
        """
        self._img = img
        self._widget_last_width = widget.width()

        new_img = img.scaledToWidth(self._widget_last_width, Qt.SmoothTransformation)
        self._pixmap = QPixmap(new_img)

        self._widget = widget
        self._radius = radius

    @classmethod
    def from_img_data(cls, img_data, *args, **kwargs):
        img = QImage()
        img.loadFromData(img_data)
        return cls(img, *args, **kwargs)

    def get_img(self) -> QImage:
        return self._img

    def get_pixmap(self) -> QPixmap:
        return self._pixmap

    def maybe_update_pixmap(self):
        if self._widget.width() != self._widget_last_width:
            self._widget_last_width = self._widget.width()
            new_img = self._img.scaledToWidth(self._widget_last_width,
                                              Qt.SmoothTransformation)
            self._pixmap = QPixmap(new_img)

    def draw(self, painter):
        if self._pixmap is None:
            return

        self.maybe_update_pixmap()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        brush = QBrush(self._pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        radius = self._radius
        size = self._pixmap.size()
        y = (size.height() - self._widget.height()) // 2

        painter.save()
        painter.translate(0, -y)
        rect = QRect(0, y, self._widget.width(), self._widget.height())
        if radius == 0:
            painter.drawRect(rect)
        else:
            radius = radius if self._radius >= 1 else self._widget.width() * self._radius
            painter.drawRoundedRect(rect, radius, radius)
        painter.restore()
        painter.restore()


class AvatarIconDrawer:
    def __init__(self, length, padding, fg_color=None):
        self._length = length
        self._padding = padding

        self.fg_color = fg_color

    def draw(self, painter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)

        if self.fg_color:
            painter.setPen(QColor(self.fg_color))

        diameter = self._length // 3
        # Draw circle.
        painter.drawEllipse(diameter, self._padding, diameter, diameter)
        # Draw body.
        x, y = self._padding, self._length // 2
        width, height = self._length // 2, self._length // 2
        painter.drawArc(x, y, width, height, 0, 60*16)
        painter.drawArc(x, y, width, height, 120*16, 60*16)
