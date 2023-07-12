from PyQt5.QtCore import QPoint, Qt, QRect, QRectF
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOptionButton
from PyQt5.QtGui import QPainter, QPalette

from feeluown.gui.helpers import darker_or_lighter


class SelfPaintAbstractButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # It seems macOS platform does not turn this attribute on by default.
        # The following two attrs are only needed on macOS, and they don't
        # cause any side effects on other platforms.
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect, True)

    def paintEvent(self, _):
        raise NotImplementedError('paintEvent must be implemented')

    def paint_border_bg_when_hover(self, painter, radius=3):
        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        if opt.state & QStyle.State_MouseOver:
            painter.save()
            painter.setPen(Qt.NoPen)
            color = self.palette().color(QPalette.Background)
            painter.setBrush(darker_or_lighter(color, 120))
            painter.drawRoundedRect(self.rect(), radius, radius)
            painter.restore()


class SelfPaintAbstractIconTextButton(SelfPaintAbstractButton):
    def __init__(self, text, height=30, padding=0.25, parent=None):
        super().__init__(parent=parent)

        self._padding = int(height * padding) if padding < 1 else padding
        self._text_width = self.fontMetrics().horizontalAdvance(text)
        self._text = text

        self.setFixedHeight(height)
        self.setMinimumWidth(height + self._text_width)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.paint_border_bg_when_hover(painter)
        self.draw_icon(painter)
        self.draw_text(painter)

    def draw_text(self, painter):
        text_rect = QRectF(self.height(), 0,
                           self.width()-self.height()-self._padding, self.height())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._text)

    def draw_icon(self, painter):
        raise NotImplementedError


class SelfPaintAbstractSquareButton(SelfPaintAbstractButton):
    def __init__(self, length=30, padding=0.25, parent=None):
        """
        All buttons should has similar paddings.
        """
        super().__init__(parent)
        self._padding = int(length * padding) if padding < 1 else padding
        self.setFixedSize(length, length)

    def paint_round_bg_when_hover(self, painter):
        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        if opt.state & QStyle.State_MouseOver:
            painter.save()
            painter.setPen(Qt.NoPen)
            color = self.palette().color(QPalette.Background)
            painter.setBrush(darker_or_lighter(color, 120))
            painter.drawEllipse(self.rect())
            painter.restore()


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
        self.paint_round_bg_when_hover(painter)

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
        self.paint_round_bg_when_hover(painter)

        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)
        # When the button size is very large, the line and the ellipse
        # will not be together.
        painter.drawEllipse(QRect(self._top_left, self._center))
        painter.drawLine(self._center, self._bottom_right)


class SettingsButton(SelfPaintAbstractSquareButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setToolTip('配置')

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)

        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        x = self.width() // 2
        painter.drawPoint(QPoint(x, int(self.width() * 0.3)))
        painter.drawPoint(QPoint(x, int(self.width() * 0.5)))
        painter.drawPoint(QPoint(x, int(self.width() * 0.7)))


class RecentlyPlayedButton(SelfPaintAbstractIconTextButton):
    def __init__(self, *args, **kwargs):
        super().__init__('最近播放', *args, **kwargs)

    def draw_icon(self, painter):
        pen_width = 1.5
        pen = painter.pen()
        pen.setWidthF(pen_width)
        painter.setPen(pen)

        x = y = self._padding
        length = self.height() - self._padding * 2
        center = self.height() // 2
        icon_rect = QRect(x, y, length, length)
        spacing = int(pen_width) + 3
        painter.drawArc(icon_rect, 250*16, 280 * 16)
        painter.drawLine(
            QPoint(center, center),
            QPoint(self.height()-self._padding-spacing-self._padding//3, center))
        painter.drawLine(QPoint(center, center),
                         QPoint(center, self._padding+spacing))
        pen.setWidthF(pen_width * 2)
        painter.setPen(pen)
        painter.drawPoint(QPoint(self._padding, center))


class HomeIcon:
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


class HomeButton(SelfPaintAbstractIconTextButton):
    def __init__(self, *args, **kwargs):
        super().__init__('主页', *args, **kwargs)
        self.home_icon = HomeIcon(self.height(), self._padding)

    def draw_icon(self, painter):
        self.home_icon.paint(painter)


if __name__ == '__main__':
    from feeluown.gui.debug import simple_layout

    length = 40

    with simple_layout() as layout:
        layout.addWidget(LeftArrowButton(length=length))
        right = RightArrowButton(length=length)
        right.setDisabled(True)
        layout.addWidget(right)
        layout.addWidget(SearchButton(length=length))
        layout.addWidget(SettingsButton(length=length))
        layout.addWidget(RecentlyPlayedButton(height=length))
        layout.addWidget(HomeButton(height=length))
