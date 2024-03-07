import math
from typing import Optional

from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QPainter, QBrush, QPixmap, QImage, QColor, QPolygonF, QPalette
from PyQt5.QtWidgets import QWidget

from feeluown.gui.helpers import random_solarized_color, painter_save


class PixmapDrawer:
    """Draw pixmap on a widget with radius.

    The pixmap will be scaled to the width of the widget.
    """
    def __init__(self, img, widget: QWidget, radius: int = 0):
        """
        :param widget: a object which has width() and height() method.
        """
        self._widget_last_width = widget.width()
        self._widget = widget
        self._radius = radius

        if img is None:
            self._color = random_solarized_color()
            self._img = None
            self._pixmap = None
        else:
            self._img = img
            self._color = None
            new_img = img.scaledToWidth(self._widget_last_width, Qt.SmoothTransformation)
            self._pixmap = QPixmap(new_img)

    @classmethod
    def from_img_data(cls, img_data, *args, **kwargs):
        img = QImage()
        img.loadFromData(img_data)
        return cls(img, *args, **kwargs)

    def get_img(self) -> Optional[QImage]:
        return self._img

    def get_pixmap(self) -> Optional[QPixmap]:
        return self._pixmap

    def maybe_update_pixmap(self):
        if self._widget.width() != self._widget_last_width:
            self._widget_last_width = self._widget.width()
            assert self._img is not None
            new_img = self._img.scaledToWidth(self._widget_last_width,
                                              Qt.SmoothTransformation)
            self._pixmap = QPixmap(new_img)

    def draw(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if self._pixmap is None:
            self._draw_random_color(painter)
        else:
            self._draw_pixmap(painter)
        painter.restore()

    def _get_radius(self):
        return self._radius if self._radius >= 1 else self._widget.width() * self._radius

    def _draw_random_color(self, painter: QPainter):
        brush = QBrush(self._color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        rect = self._widget.rect()
        if self._radius == 0:
            painter.drawRect(rect)
        else:
            radius = self._get_radius()
            painter.drawRoundedRect(rect, radius, radius)

    def _draw_pixmap(self, painter: QPainter):
        assert self._pixmap is not None

        self.maybe_update_pixmap()
        brush = QBrush(self._pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        radius = self._radius
        size = self._pixmap.size()
        y = (size.height() - self._widget.height()) // 2
        painter.save()
        painter.translate(0, -y)
        rect = QRect(0, 0, self._widget.width(), size.height())
        if radius == 0:
            painter.drawRect(rect)
        else:
            radius = radius if self._radius >= 1 else self._widget.width() * self._radius
            painter.drawRoundedRect(rect, radius, radius)
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


class SearchIconDrawer:
    def __init__(self, length, padding):
        t_l_x = t_l_y = padding
        b_r_x = b_r_y = length - padding
        center = int(length * 0.6)
        self._bottom_right = QPoint(b_r_x, b_r_y)
        self._top_left = QPoint(t_l_x, t_l_y)
        self._center = QPoint(center, center)

    def draw(self, painter: QPainter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawEllipse(QRect(self._top_left, self._center))
        painter.drawLine(self._center, self._bottom_right)


class TriangleIconDrawer:
    def __init__(self, length, padding, direction='up', brush=False):
        self._length = length
        self._padding = padding
        self.brush = brush

        # initialized when direction is set
        # polygon points are orgonized in anticlockwise direction
        self.triangle = QPolygonF([])
        self.set_direction(direction)

    def set_direction(self, direction):
        length = self._length
        padding = self._padding

        half = length / 2
        diameter = length - 2 * padding

        real_padding = (length - diameter) / 2
        center_top = QPointF(half, real_padding)
        center_bottom = QPointF(half, real_padding + diameter)
        left = QPointF(real_padding, half)
        right = QPointF(real_padding + diameter, half)

        d60 = diameter / 2 * 0.87  # sin60
        d30 = diameter / 2 / 2    # sin30

        if direction in ('left', 'right'):
            left_x = half - d30
            top_y = half - d60
            bottom_y = half + d60
            right_x = half + d30
        else:
            left_x = half - d60
            top_y = half - d30
            bottom_y = half + d30
            right_x = half + d60

        left_top = QPointF(left_x, top_y)
        left_bottom = QPointF(left_x, bottom_y)
        right_top = QPointF(right_x, top_y)
        right_bottom = QPointF(right_x, bottom_y)

        if direction == 'up':
            self.triangle = QPolygonF([center_top, left_bottom, right_bottom])
        elif direction == 'down':
            self.triangle = QPolygonF([center_bottom, right_top, left_top])
        elif direction == 'left':
            self.triangle = QPolygonF([left, right_bottom, right_top])
        elif direction == 'right':
            self.triangle = QPolygonF([right, left_top, left_bottom])
        else:
            raise ValueError('direction must be one of up/down/left/right')

    def draw(self, painter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        with painter_save(painter):
            if self.brush is True:
                painter.setBrush(pen.color())
            painter.drawPolygon(self.triangle)


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


class CalendarIconDrawer:
    def __init__(self, length, padding):
        self._body_x = self._body_y = padding
        self._body_width = length - 2 * padding
        self._radius = 3
        self._h_line_y = self._body_y + self._body_width // 4

    def paint(self, painter: QPainter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        body_rect = QRect(self._body_x, self._body_x, self._body_width, self._body_width)
        painter.drawRoundedRect(body_rect, self._radius, self._radius)
        painter.drawLine(QPoint(self._body_x, self._h_line_y),
                         QPoint(self._body_x + self._body_width, self._h_line_y))


class RankIconDrawer:
    def __init__(self, length, padding):
        body = length - 2*padding
        body_2 = body // 2
        body_8 = body // 8
        body_3 = body // 3
        _top_right_x = length - padding
        _top_right_y = padding + body_8
        _bottom_left_y = padding + body - body_8

        self.p1 = QPoint(padding, _bottom_left_y)
        self.p2 = QPoint(padding + body_3, padding + body_3)
        self.p3 = QPoint(padding + body_2, padding + body_3 * 2)
        self.p4 = QPoint(_top_right_x, _top_right_y)
        self.p5 = QPoint(_top_right_x - body_3, _top_right_y)
        self.p6 = QPoint(_top_right_x, _top_right_y + body_3)

    def paint(self, painter: QPainter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(self.p1, self.p2)
        painter.drawLine(self.p2, self.p3)
        painter.drawLine(self.p3, self.p4)
        painter.drawLine(self.p4, self.p5)
        painter.drawLine(self.p4, self.p6)


class StarIconDrawer:
    def __init__(self, length, padding):

        radius_outer = (length - 2*padding)//2
        length_half = length // 2
        radius_inner = radius_outer // 2
        center = QPointF(length_half, length_half)
        angle = math.pi / 2

        self._star_polygon = QPolygonF()
        for _ in range(5):
            outer_point = center + QPointF(
                radius_outer * math.cos(angle),
                -radius_outer * math.sin(angle)
            )
            self._star_polygon.append(outer_point)
            inner_point = center + QPointF(
                radius_inner * math.cos(angle + math.pi/5),
                -radius_inner * math.sin(angle + math.pi/5)
            )
            self._star_polygon.append(inner_point)
            angle += 2 * math.pi / 5

    def paint(self, painter: QPainter):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawPolygon(self._star_polygon)


class VolumeIconDrawer:
    def __init__(self, length, padding):
        self._polygon = QPolygonF()
        self._padding = padding
        self._volume = 100

        body_length = length - 2 * padding
        body_length_4_1 = 0.25 * body_length
        body_length_2_1 = 0.5 * body_length
        body_length_4_3 = 0.75 * body_length
        body_length_3_1 = 0.33 * body_length
        body_length_3_2 = 0.66 * body_length

        left_top = QPointF(0, body_length_4_1)
        left_bottom = QPointF(0, body_length_4_3)
        mid_top = QPointF(body_length_3_1, body_length_4_1)
        mid_bottom = QPointF(body_length_3_1, body_length_4_3)
        right_top = QPointF(body_length_3_2, 0)
        right_bottom = QPointF(body_length_3_2, body_length)

        for p in (left_top, left_bottom, mid_bottom, right_bottom,
                  right_top, mid_top):
            self._polygon.append(p)

        line_right_top_y = 0.1 * body_length
        line_right_bottom_y = 0.9 * body_length
        line_left_top_y = 0.2 * body_length
        line_left_bottom_y = 0.8 * body_length
        line_left_x = 0.85 * body_length
        self._line1 = (QPointF(line_left_x, line_left_top_y),
                       QPointF(body_length, line_right_top_y))
        self._line2 = (QPointF(line_left_x, body_length_2_1),
                       QPointF(body_length, body_length_2_1))
        self._line3 = (QPointF(line_left_x, line_left_bottom_y),
                       QPointF(body_length, line_right_bottom_y))

    def get_volume(self):
        return self._volume

    def set_volume(self, volume):
        self._volume = volume

    def draw(self, painter: QPainter, palette: QPalette):
        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        with painter_save(painter):
            painter.translate(self._padding, self._padding)
            painter.drawPolygon(self._polygon)

            if self._volume >= 66:
                lines = (self._line1, self._line2, self._line3)
                disabled_lines = ()
            elif self._volume >= 33:
                lines = (self._line2, self._line3)
                disabled_lines = (self._line1, )
            elif self._volume > 0:
                lines = (self._line3, )
                disabled_lines = (self._line1, self._line2)
            else:
                lines = ()
                disabled_lines = (self._line1, self._line2, self._line3)
            for line in lines:
                painter.drawLine(*line)
            pen = painter.pen()
            pen.setColor(palette.color(QPalette.Disabled, QPalette.ButtonText))
            painter.setPen(pen)
            for line in disabled_lines:
                painter.drawLine(*line)
