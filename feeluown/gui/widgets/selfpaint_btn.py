from PyQt5.QtCore import QPoint, Qt, QRect
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOptionButton
from PyQt5.QtGui import QPainter, QPalette

from feeluown.gui.helpers import darker_or_lighter


class SelfPaintAbstractSquareButton(QPushButton):
    def __init__(self, length=30, padding=0.25, parent=None):
        """
        All buttons should has similar paddings.
        """
        super().__init__(parent)
        self._padding = int(length * padding) if padding < 1 else padding
        self.setFixedSize(length, length)

    def paintEvent(self, _):
        raise NotImplementedError('paintEvent must be implemented')


def paint_round_bg_when_hover(widget, painter):
    opt = QStyleOptionButton()
    widget.initStyleOption(opt)

    if opt.state & QStyle.State_MouseOver:
        painter.save()
        painter.setPen(Qt.NoPen)
        color = widget.palette().color(QPalette.Background)
        painter.setBrush(darker_or_lighter(color, 120))
        painter.drawEllipse(widget.rect())
        painter.restore()


class HomeButton(SelfPaintAbstractSquareButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        width, height = self.width(), self.height()
        diff = 1  # root/body width diff
        h_padding = v_padding = self._padding

        body_left_x = h_padding + diff*2
        body_right_x = width - h_padding - diff*2
        body_top_x = height // 2

        self._roof = QPoint(width // 2, v_padding)
        self._root_left = QPoint(h_padding, height // 2 + diff)
        self._root_right = QPoint(width - h_padding, height // 2 + diff)

        self._body_bottom_left = QPoint(body_left_x, height - v_padding)
        self._body_bottom_right = QPoint(body_right_x, height - v_padding)
        self._body_top_left = QPoint(body_left_x, body_top_x)
        self._body_top_right = QPoint(body_right_x, body_top_x)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(self._roof, self._root_left)
        painter.drawLine(self._roof, self._root_right)
        painter.drawLine(self._body_bottom_left, self._body_bottom_right)
        painter.drawLine(self._body_top_left, self._body_bottom_left)
        painter.drawLine(self._body_top_right, self._body_bottom_right)


class ArrowAbstractButton(SelfPaintAbstractSquareButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        width = self.width()
        half = width // 2
        half_half = half // 2
        self._top = QPoint(half, half_half)
        self._left = QPoint(half_half, half)
        self._right = QPoint(half_half + half, half)
        self._bottom = QPoint(half, half + half_half)

        self.vertexes = [self._top, self._left, self._right, self._bottom]

    @property
    def cross(self):
        raise NotImplementedError

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        for vertex in self.vertexes:
            if vertex != self.cross:
                painter.drawLine(self.cross, vertex)


class LeftArrowButton(ArrowAbstractButton):
    @property
    def cross(self):
        return self._left


class RightArrowButton(ArrowAbstractButton):
    @property
    def cross(self):
        return self._right


class SearchButton(SelfPaintAbstractSquareButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        t_l_x = t_l_y = self._padding
        b_r_x = b_r_y = self.width() - self._padding
        center = int(self.width() * 0.6)
        self._bottom_right = QPoint(b_r_x, b_r_y)
        self._top_left = QPoint(t_l_x, t_l_y)
        self._center = QPoint(center, center)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        # When the button size is very large, the line and the ellipse
        # will not be together.
        painter.drawEllipse(QRect(self._top_left, self._center))
        painter.drawLine(self._center, self._bottom_right)


class SettingsButton(SelfPaintAbstractSquareButton):
    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        x = self.width() // 2
        painter.drawPoint(QPoint(x, int(self.width() * 0.3)))
        painter.drawPoint(QPoint(x, int(self.width() * 0.5)))
        painter.drawPoint(QPoint(x, int(self.width() * 0.7)))


if __name__ == '__main__':
    from feeluown.gui.debug import simple_layout

    length = 40

    with simple_layout() as layout:
        layout.addWidget(LeftArrowButton(length=length))
        layout.addWidget(HomeButton(length=length))
        right = RightArrowButton(length=length)
        right.setDisabled(True)
        layout.addWidget(right)
        layout.addWidget(SearchButton(length=length))
        layout.addWidget(SettingsButton(length=length))
