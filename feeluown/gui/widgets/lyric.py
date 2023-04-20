import sys

from PyQt5.QtCore import Qt, QRectF, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QTextOption, QPainter, \
    QKeySequence, QFont
from PyQt5.QtWidgets import QLabel, QWidget,\
    QVBoxLayout, QSizeGrip, QHBoxLayout, QColorDialog, \
    QMenu, QAction, QFontDialog, QShortcut

from feeluown.gui.helpers import resize_font, elided_text
from feeluown.player import LyricLine


IS_MACOS = sys.platform == 'darwin'


def set_bg_color(palette, color):
    palette.setColor(QPalette.Active, QPalette.Window, color)
    palette.setColor(QPalette.Active, QPalette.Base, color)
    palette.setColor(QPalette.Inactive, QPalette.Window, color)
    palette.setColor(QPalette.Inactive, QPalette.Base, color)


def set_fg_color(palette, color):
    palette.setColor(QPalette.Active, QPalette.WindowText, color)
    palette.setColor(QPalette.Active, QPalette.Text, color)
    palette.setColor(QPalette.Inactive, QPalette.WindowText, color)
    palette.setColor(QPalette.Inactive, QPalette.Text, color)


class LyricWindow(QWidget):

    play_previous_needed = pyqtSignal()
    play_next_needed = pyqtSignal()

    def __init__(self, app):
        super().__init__(parent=None)
        self._app = app

        if IS_MACOS:
            # On macOS, Qt.Tooltip widget can't accept focus and it will hide
            # when the application window is actiavted. Qt.Tool widget can't
            # keep staying on top. Neither of them work well on macOS.
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        else:
            # TODO: use proper flags on other platforms
            # see #413 for more details
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.c = Container(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.c)

        self._old_pos = None

        QShortcut(QKeySequence.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.ZoomOut, self).activated.connect(self.zoomout)
        QShortcut(QKeySequence('Ctrl+='), self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)

        self.setToolTip('''
* 右键可以弹出设置菜单
* Ctrl+= 或者 Ctrl++ 可以增大字体
* Ctrl+- 可以减小字体
* 鼠标前进后退键可以播放前一首/下一首
''')

    def set_line(self, line: LyricLine):
        if self.isVisible():
            self.c.line_label.set_line(line)

    def mousePressEvent(self, e):
        self._old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._old_pos is not None:
            delta = e.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = e.globalPos()

    def mouseReleaseEvent(self, e):
        if not self.rect().contains(e.pos()):
            return
        if e.button() == Qt.BackButton:
            self.play_previous_needed.emit()
        elif e.button() == Qt.ForwardButton:
            self.play_next_needed.emit()

    def showEvent(self, e) -> None:
        self.set_line(self._app.live_lyric.current_line)
        return super().showEvent(e)

    def zoomin(self):
        label = self.c.line_label
        font = label.font()
        resize_font(font, +1)
        label.setFont(font)

    def zoomout(self):
        label = self.c.line_label
        font = label.font()
        resize_font(font, - 1)
        label.setFont(font)

    def dump_state(self):
        p = self.c.line_label.palette()
        geo = self.geometry()
        return {
            'geometry': (geo.x(), geo.y(), geo.width(), geo.height()),
            'font': self.c.line_label.font().toString(),
            'bg': p.color(QPalette.Active, QPalette.Window).name(QColor.HexArgb),
            'fg': p.color(QPalette.Active, QPalette.Text).name(QColor.HexArgb),
        }

    def apply_state(self, state):
        if not state:
            return

        geo = state.get('geometry', None)
        if geo:
            self.setGeometry(*geo)

        font = self.c.line_label.font()
        font.fromString(state['font'])
        self.c.line_label.setFont(font)

        p = self.c.line_label.palette()
        set_bg_color(p, QColor(state['bg']))
        set_fg_color(p, QColor(state['fg']))
        self.c.line_label.setPalette(p)

    def sizeHint(self):
        return QSize(500, 60)


class SentenceLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAlignment(Qt.AlignBaseline | Qt.AlignVCenter | Qt.AlignHCenter)
        self.setWordWrap(False)


class LineLabel(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = SentenceLabel('...', self)
        self.trans_label = SentenceLabel('...', self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(5)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self.trans_label)
        self._layout.addSpacing(5)

        font = self.font()
        font.setPixelSize(25)
        self.setFont(font)

    def set_line(self, line: LyricLine):
        o = elided_text(line.origin, self.width(), self.font())
        self.label.setText(o)
        if line.has_trans:
            self.trans_label.show()
            t = elided_text(line.trans, self.width(), self.font())
            self.trans_label.setText(t)
        else:
            self.trans_label.hide()

    def setFont(self, font):
        super().setFont(font)

        font.setBold(True)
        self.label.setFont(font)
        font2 = QFont(font)
        font2.setBold(False)
        resize_font(font2, -8)
        self.trans_label.setFont(font2)

    def setPalette(self, palette):
        super().setPalette(palette)
        self.label.setPalette(palette)
        self.trans_label.setPalette(palette)


class Container(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._border_radius = 10
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedWidth(self._border_radius * 2)
        self.line_label = LineLabel(self)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(self._border_radius * 2)
        self._layout.addWidget(self.line_label)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignBottom)

    def paintEvent(self, e):
        """
        Draw some text to make the size_grip more obvious.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        painter.save()
        painter.setPen(QColor('white'))
        option = QTextOption()
        option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        rect = QRect(self.mapToParent(self._size_grip.pos()), self._size_grip.size())
        painter.drawText(QRectF(rect), '●', option)
        painter.restore()

    def setPalette(self, a0: QPalette) -> None:
        super().setPalette(a0)
        self.line_label.setPalette(a0)

    def setFont(self, a0: QFont) -> None:
        super().setFont(a0)
        self.line_label.setFont(a0)

    def show_color_dialog(self, bg=True):
        def set_color(color):
            palette = self.palette()
            if bg:
                set_bg_color(palette, color)
            else:
                set_fg_color(palette, color)
            self.setPalette(palette)

        dialog = QColorDialog(self)
        if bg:
            color = self.palette().color(QPalette.Window)
        else:
            color = self.palette().color(QPalette.Text)
        dialog.setCurrentColor(color)
        dialog.currentColorChanged.connect(set_color)
        dialog.colorSelected.connect(set_color)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        dialog.exec()

    def show_font_dialog(self):
        dialog = QFontDialog(self.font(), self)
        dialog.currentFontChanged.connect(self.setFont)
        dialog.fontSelected.connect(self.setFont)
        dialog.exec()

    def contextMenuEvent(self, e):
        menu = QMenu()
        bg_color_action = QAction('背景颜色', menu)
        fg_color_action = QAction('文字颜色', menu)
        font_action = QAction('字体', menu)
        menu.addAction(bg_color_action)
        menu.addAction(fg_color_action)
        menu.addSeparator()
        menu.addAction(font_action)
        bg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=True))
        fg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=False))
        font_action.triggered.connect(self.show_font_dialog)
        menu.exec(e.globalPos())
