from PyQt5.QtCore import QPoint, Qt, QRect, QRectF, QTimer, QPointF
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOptionButton
from PyQt5.QtGui import QPainter, QPalette, QPainterPath

from feeluown.gui.drawers import (
    HomeIconDrawer,
    PlusIconDrawer,
    TriangleIconDrawer,
    CalendarIconDrawer,
    RankIconDrawer,
    StarIconDrawer,
    VolumeIconDrawer,
    SearchIconDrawer,
    FireIconDrawer,
    EmojiIconDrawer,
    AIIconDrawer,
)
from feeluown.gui.helpers import darker_or_lighter, painter_save


def set_pen_width(painter, width):
    pen = painter.pen()
    pen.setWidthF(width)
    painter.setPen(pen)


def set_pen_1_5(painter):
    set_pen_width(painter, 1.5)


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

    def hitButton(self, pos: QPoint) -> bool:
        # QPushButton use style().subElementRect().contains to check if it is hit.
        # style().subElementRect is really small for buttons. So it does not
        # work well for small buttons (tested on macOS).
        return self.rect().contains(pos)

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

    def __init__(self, text='', height=30, padding=0.25, parent=None):
        super().__init__(parent=parent)

        self._padding: int = int(height * padding if padding < 1 else padding)
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
        text_rect = QRectF(
            self.height(), 0,
            self.width() - self.height() - self._padding, self.height()
        )
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._text)

    def draw_icon(self, painter):
        raise NotImplementedError


class SelfPaintAbstractSquareButton(SelfPaintAbstractButton):

    def __init__(self, length=30, padding=0.25, parent=None):
        """
        All buttons should has similar paddings.
        """
        super().__init__(parent)
        self._padding = int(length * padding) if padding < 1 else int(padding)
        self._body_width = length - 2 * self._padding
        self._body_rect = QRect(
            self._padding, self._padding, self._body_width, self._body_width
        )
        self.setFixedSize(length, length)

    def paint_round_bg(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)
        color = self.palette().color(QPalette.Background)
        painter.setBrush(darker_or_lighter(color, 120))
        painter.drawEllipse(self.rect())
        painter.restore()

    def paint_round_bg_when_hover(self, painter):
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        if opt.state & QStyle.State_MouseOver:
            self.paint_round_bg(painter)


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
        set_pen_1_5(painter)
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


class SearchSwitchButton(SelfPaintAbstractSquareButton):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._plus_drawer = PlusIconDrawer(self.width(), self._padding)
        self._search_drawer = SearchIconDrawer(self.width(), self._padding)
        # 0.21 = 1.414 / 2 - 0.5
        self._translate_p = QPoint(self.width()//2, -int(self.width()*0.21))

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)

        # When the button size is very large, the line and the ellipse
        # will not be together.
        if self.isChecked():
            with painter_save(painter):
                painter.translate(self._translate_p)
                painter.rotate(45)
                self._plus_drawer.draw(painter)
        else:
            self._search_drawer.draw(painter)


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


class PlusButton(SelfPaintAbstractSquareButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.drawer = PlusIconDrawer(self.width(), self._padding)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        self.drawer.draw(painter)


class TriagleButton(SelfPaintAbstractSquareButton):

    def __init__(self, direction='up', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drawer = TriangleIconDrawer(
            self.width(), self._padding, direction=direction
        )

    def set_direction(self, direction):
        self.drawer.set_direction(direction)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        self.drawer.draw(painter)


class RecentlyPlayedButton(SelfPaintAbstractIconTextButton):

    def __init__(self, text='最近播放', **kwargs):
        super().__init__(text, **kwargs)

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
        painter.drawArc(icon_rect, 250 * 16, 280 * 16)
        painter.drawLine(
            QPoint(center, center),
            QPoint(self.height() - self._padding - spacing - self._padding // 3, center)
        )
        painter.drawLine(QPoint(center, center), QPoint(center, self._padding + spacing))
        pen.setWidthF(pen_width * 2)
        painter.setPen(pen)
        painter.drawPoint(QPoint(self._padding, center))


class AIButton(SelfPaintAbstractIconTextButton):

    def __init__(self, *args, **kwargs):
        super().__init__('AI', *args, **kwargs)
        self.ai_icon = AIIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.ai_icon.draw(painter, self.palette())


class DiscoveryButton(SelfPaintAbstractIconTextButton):

    def __init__(self, text='发现', **kwargs):
        super().__init__(text=text, **kwargs)

        self._timer = QTimer(self)

        length = self.height()
        self._half = length // 2
        self._v1 = self._half - self._padding
        self._v2 = self._v1 / 2.5

        self._triagle = QPainterPath(QPointF(-self._v2, 0))
        self._triagle.lineTo(QPointF(0, self._v1))
        self._triagle.lineTo(QPointF(0, self._v2))
        self._rotate = 0
        self._rotate_mod = 360

        # self._timer.timeout.connect(self.on_timeout)
        # self._timer.start(30)

    def on_timeout(self):
        self._rotate = (self._rotate + 2) % self._rotate_mod
        self.update()

    def draw_icon(self, painter: QPainter):
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        set_pen_1_5(painter)
        painter.save()
        painter.translate(self._half, self._half)
        painter.rotate(self._rotate)
        for ratio in range(4):
            painter.rotate(90 * ratio)
            painter.drawPath(self._triagle)
        painter.restore()


class HomeButton(SelfPaintAbstractIconTextButton):

    def __init__(self, *args, **kwargs):
        super().__init__('主页', *args, **kwargs)
        self.home_icon = HomeIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.home_icon.paint(painter)


class CalendarButton(SelfPaintAbstractIconTextButton):

    def __init__(self, text='日历', *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.calendar_icon = CalendarIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.calendar_icon.paint(painter)


class RankButton(SelfPaintAbstractIconTextButton):

    def __init__(self, text='排行榜', *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.rank_icon = RankIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.rank_icon.paint(painter)


class StarButton(SelfPaintAbstractIconTextButton):

    def __init__(self, text='收藏', *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.star_icon = StarIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.star_icon.paint(painter)


class HotButton(SelfPaintAbstractIconTextButton):
    def __init__(self, text='热门', *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.hot_icon = FireIconDrawer(self.height(), self._padding)

    def draw_icon(self, painter):
        self.hot_icon.paint(painter)


class EmojiButton(SelfPaintAbstractIconTextButton):
    def __init__(self, emoji: str, text='表情', *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.emoji_icon = EmojiIconDrawer(emoji, self.height(), self._padding)

    def draw_icon(self, painter):
        self.emoji_icon.paint(painter)


class PlayButton(SelfPaintAbstractSquareButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.drawer = TriangleIconDrawer(
            self.width(), self._padding, direction='right', brush=True
        )

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        self.drawer.draw(painter)


class PlayPauseButton(SelfPaintAbstractSquareButton):

    def __init__(self, *args, draw_circle=True, **kwargs):
        super().__init__(*args, **kwargs)

        self._draw_circle = draw_circle
        self.setCheckable(True)
        self.drawer = TriangleIconDrawer(
            self.width(), self._padding, direction='right', brush=True
        )
        self._radius = self.width() // 2

        # Calculate line rect properties.
        p0 = self.drawer.triangle[0]
        p1 = self.drawer.triangle[1]
        p2 = self.drawer.triangle[2]
        small_y = min(p1.y(), p2.y())
        big_y = max(p1.y(), p2.y())
        height = big_y - small_y
        x = p0.x()
        x2 = p1.x()
        x_move = abs(x2 - x) / 8
        self._line_half_width = 1
        self._line1_rect = QRectF(
            x - x_move - self._line_half_width, small_y, self._line_half_width * 2,
            height
        )
        self._line2_rect = QRectF(
            x2 + x_move - self._line_half_width, small_y, self._line_half_width * 2,
            height
        )
        self._translate_x = -0.125 * self._body_width
        self._pen_width = 1.5
        self._inner_rect = QRectF(
            self._pen_width, self._pen_width,
            self.width() - 2 * self._pen_width,
            self.height() - 2 * self._pen_width
        )

    def set_draw_circle(self, draw_circle: bool):
        self._draw_circle = draw_circle
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        set_pen_width(painter, self._pen_width)
        self.paint_round_bg_when_hover(painter)
        if self.isChecked():
            with painter_save(painter):
                painter.translate(self._translate_x, 0)
                painter.setBrush(painter.pen().color())
                painter.drawRoundedRect(
                    self._line1_rect, self._line_half_width, self._line_half_width
                )
                painter.drawRoundedRect(
                    self._line2_rect, self._line_half_width, self._line_half_width
                )
        else:
            self.drawer.draw(painter)
        if self._draw_circle is True:
            painter.drawEllipse(self._inner_rect)


class _PlayXButton(SelfPaintAbstractSquareButton):

    def __init__(self, direction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drawer = TriangleIconDrawer(
            self.width(), self._padding, direction=direction, brush=False
        )
        p0 = self.drawer.triangle[0]
        p1 = self.drawer.triangle[1]
        p2 = self.drawer.triangle[2]

        # When the directory is 'right'
        # left distance (before): body_width // 4
        # left distance (now): body_width//2 - body_width*0.75//2
        self._body_translate = -0.125 if direction == 'right' else 0.125

        # Line rect properties.
        small_y = min(p1.y(), p2.y())
        big_y = max(p1.y(), p2.y())
        half_width = 1.5
        height = big_y - small_y
        x = p0.x()
        self._line = QPointF(x, small_y), QPointF(x, big_y)
        self._line_rect = QRectF(x - half_width, small_y, half_width * 2, height)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        with painter_save(painter):
            painter.translate(self._body_translate * self._body_width, 0)
            self.drawer.draw(painter)
            with painter_save(painter):
                set_pen_1_5(painter)
                painter.setBrush(painter.pen().color())
                painter.drawLine(*self._line)


class PlayNextButton(_PlayXButton):

    def __init__(self, *args, **kwargs):
        super().__init__('right', *args, **kwargs)


class PlayPreviousButton(_PlayXButton):

    def __init__(self, *args, **kwargs):
        super().__init__('left', *args, **kwargs)


class MVButton(SelfPaintAbstractSquareButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rectangle_height = int(self.width() * 0.618)
        self.rectangle_y = (self.height() - self.rectangle_height) // 2
        self.drawer = TriangleIconDrawer(
            self.width(), self.width() * 0.35, direction='right', brush=True
        )

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        rect = QRect(1, self.rectangle_y, self.width() - 2, self.rectangle_height)
        with painter_save(painter):
            set_pen_1_5(painter)
            if opt.state & QStyle.State_MouseOver:
                color = self.palette().color(QPalette.Background)
                painter.setBrush(darker_or_lighter(color, 120))
            painter.drawRoundedRect(rect, 3, 3)
        self.drawer.draw(painter)


class VolumeButton(SelfPaintAbstractSquareButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.drawer = VolumeIconDrawer(self.width(), self._padding)

    def set_volume(self, volume):
        self.drawer.set_volume(volume)
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        self.drawer.draw(painter, self.palette())


if __name__ == '__main__':
    from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

    from feeluown.gui.debug import simple_layout

    length = 40

    with simple_layout(QVBoxLayout) as layout:
        l1 = QHBoxLayout()
        l2 = QHBoxLayout()
        l3 = QVBoxLayout()
        layout.addLayout(l1)
        layout.addLayout(l2)
        layout.addLayout(l3)

        l1.addWidget(LeftArrowButton(length=length))
        right = RightArrowButton(length=length)
        right.setDisabled(True)
        l1.addWidget(right)
        l1.addWidget(SearchSwitchButton(length=length))
        l1.addWidget(SettingsButton(length=length))
        l1.addWidget(RecentlyPlayedButton(height=length))

        l1.addWidget(TriagleButton(length=length, direction='up'))
        l1.addWidget(CalendarButton(height=length))

        l2.addWidget(PlayPreviousButton(length=length))
        l2.addWidget(PlayPauseButton(length=60))
        l2.addWidget(PlayNextButton(length=length))
        volume_button = VolumeButton(length=length)
        volume_button.set_volume(60)
        l2.addWidget(volume_button)
        l2.addStretch(0)

        l3.addWidget(HotButton(height=length))
        l3.addWidget(HomeButton(height=length))
        l3.addWidget(AIButton(height=length))
        l3.addWidget(DiscoveryButton(height=length))
        l3.addWidget(RankButton(height=length))
        l3.addWidget(StarButton(height=length))
        l3.addWidget(EmojiButton('😁', '开心', height=length))
        l3.addWidget(EmojiButton('🔥', '热门', height=length))
        l3.addStretch(0)
