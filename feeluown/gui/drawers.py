from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QPainter, QBrush, QPixmap, QImage, QColor, QPolygonF
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


class PlusIconDrawer:
    def __init__(self, length, padding):
        self.top = QPoint(length//2, padding)
        self.bottom = QPoint(length//2, length - padding)
        self.left = QPoint(padding, length//2)
        self.right = QPoint(length-padding, length//2)

    def draw(self, painter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(self.top, self.bottom)
        painter.drawLine(self.left, self.right)


class TriangleIconDrawer:
    def __init__(self, length, padding, direction='up'):
        self._length = length
        self._padding = padding
        self.set_direction(direction)

    def set_direction(self, direction):
        length = self._length
        padding = self._padding

        half = length / 2
        diameter = (length - 2 * padding) * 1.2
        d60 = diameter / 2 * 0.87  # sin60
        d30 = diameter / 2 / 2    # sin30

        half_d30 = half - d30
        half_d60 = half - d60
        half_p_d60 = half + d60
        half_p_d30 = half + d30
        l_p = length - padding

        center_top = QPointF(half, padding)
        center_bottom = QPointF(half, l_p)
        left = QPointF(padding, half)
        right = QPointF(l_p, half)
        left_top = QPointF(half_d30, half_d60)
        left_bottom = QPointF(half_d60, half_p_d30)
        right_top = QPointF(half_p_d30, half_p_d60)
        right_bottom = QPointF(half_p_d60, half_p_d30)

        if direction == 'up':
            self._triangle = QPolygonF([center_top, left_bottom, right_bottom])
        elif direction == 'down':
            self._triangle = QPolygonF([center_bottom, left_top, right_top])
        elif direction == 'left':
            self._triangle = QPolygonF([left, right_top, right_bottom])
        elif direction == 'right':
            self._triangle = QPolygonF([right, left_top, left_bottom])
        else:
            raise ValueError('direction must be one of up/down/left/right')

    def draw(self, painter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawPolygon(self._triangle)


class HomeIconDrawer:
    def __init__(self, length, padding):
        icon_length = length
        diff = 1  # root/body width diff
        h_padding = v_padding = padding

        body_left_x = h_padding + diff*2
        body_right_x = icon_length - h_padding - diff*2
        body_top_x = icon_length // 2

        self._roof = QPoint(icon_length // 2, v_padding)
        self._root_left = QPoint(h_padding, icon_length // 2 + diff)
        self._root_right = QPoint(icon_length - h_padding, icon_length // 2 + diff)

        self._body_bottom_left = QPoint(body_left_x, icon_length - v_padding)
        self._body_bottom_right = QPoint(body_right_x, icon_length - v_padding)
        self._body_top_left = QPoint(body_left_x, body_top_x)
        self._body_top_right = QPoint(body_right_x, body_top_x)

    def paint(self, painter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(self._roof, self._root_left)
        painter.drawLine(self._roof, self._root_right)
        painter.drawLine(self._body_bottom_left, self._body_bottom_right)
        painter.drawLine(self._body_top_left, self._body_bottom_left)
        painter.drawLine(self._body_top_right, self._body_bottom_right)
