from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtGui import QTextOption, QColor, QPalette, QPainter


# https://ethanschoonover.com/solarized/
COLORS = {
    'yellow':    '#b58900',
    'orange':    '#cb4b16',
    'red':       '#dc322f',
    'magenta':   '#d33682',
    'violet':    '#6c71c4',
    'blue':      '#268bd2',
    'cyan':      '#2aa198',
    'green':     '#859900',
}


class StatusLineItem:
    """状态栏组件"""
    def __init__(self, name, widget):
        self.name = name
        self.widget = widget

    def __eq__(self, other):
        return isinstance(other, StatusLineItem) \
            and other.name == self.name \
            and other.widget is self.widget


class StatuslineLabel(QLabel):
    """
    StatuslineLabel 是一个基类，具体的设计还没想好太清楚，不建议大范围使用。

    大概想法如下：Label 由两部分组成，中间和通知部分（参考 chrome 的插件图标）。
    基类会定义好这两个部分的 size，并提供一些预定义好的绘制函数供子类使用。
    """
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app

        # TODO: 顶部导航栏中前进、后退按钮的的高度也是 30，之后应该由外部传入进来
        self._width = self._height = 30
        self._inner_width = self._inner_height = 18
        self._status_width = self._status_height = 13
        self._status_font_size = 8
        self._status_color = 'red'
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
        painter.setRenderHint(QPainter.Antialiasing)

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
        painter.setPen(Qt.NoPen)
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
        border_color = self.palette().color(QPalette.Window)
        pen.setColor(QColor(border_color))
        painter.setPen(pen)
        w = h = self._width // 2 - 2
        painter.translate(self._width - w, self._width - h)
        text_rect = QRectF(0, 0, w, h)
        text_bg_color = QColor(COLORS[self._status_color])
        text_bg_color.setAlpha(225)
        painter.setBrush(text_bg_color)
        radius = 4
        painter.drawRoundedRect(text_rect, radius, radius)
        painter.drawText(text_rect, self.text(), QTextOption(Qt.AlignCenter))
        painter.restore()


class StatusLine(QWidget):
    """状态栏（类似 Emacs/Vim status line）"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._items = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

    def add_item(self, item):
        """添加组件"""
        if item not in self._items:
            self._items.append(item)
            self._layout.addWidget(item.widget)

    def remove_item(self, item):
        """移除组件

        :param item: 一个 StatusLineItem 对象，或者 item 名字
        """
        pass
