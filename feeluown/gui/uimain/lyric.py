import sys

from PyQt5.QtCore import Qt, QRectF, QRect, QSize
from PyQt5.QtGui import QPalette, QColor, QTextOption, QPainter, \
    QKeySequence, QFont
from PyQt5.QtWidgets import QLabel, QWidget, \
    QVBoxLayout, QSizeGrip, QHBoxLayout, QColorDialog, \
    QMenu, QAction, QFontDialog, QShortcut, QSpacerItem

from feeluown.gui.helpers import esc_hide_widget, resize_font, elided_text
from feeluown.player import LyricLine


IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'


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


Tooltip = """
* 右键可以弹出设置菜单
* Ctrl+= 或者 Ctrl++ 可以增大字体
* Ctrl+- 可以减小字体
* 鼠标前进后退键可以播放前一首/下一首
* ESC 键可以关闭此歌词窗口
"""


class SizeGrip(QSizeGrip):
    """
    On windows, when the user drags the size grip, the lyric window is
    resized and the lyric window also moves. This is not the expected.
    So override the mouse event to fix this issue.

    Check https://github.com/feeluown/FeelUOwn/issues/752 for more details.
    """
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if IS_WINDOWS:
            e.accept()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        if IS_WINDOWS:
            e.accept()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if IS_WINDOWS:
            e.accept()

    def paintEvent(self, _):
        """
        On windows, it draws a icon on the corner. On other platforms, it does not.
        So let LyricWindow draw the icon for the SizeGrip.
        """
        if IS_WINDOWS:
            return


class LyricWindow(QWidget):
    """LyricWindow is a transparent container which contains a real lyric window.

    LyricWindow acts as a transparent container, so the inner window can has
    semi-transparent background. It is also responsible for handling the
    window flags and geometry. It also provides a few APIs for communicating
    with other widgets
    """

    def __init__(self, app):
        super().__init__(parent=None)
        self._app = app

        if IS_MACOS:
            # On macOS, Qt.Tooltip widget can't accept focus and it will hide
            # when the application window is actiavted. Qt.Tool widget can't
            # keep staying on top. Neither of them work well on macOS.
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        else:
            # TODO: use proper flags on other platforms, see #413 for more details.
            # User can customize the flags in the .fuorc or searchbox, like
            #    app.ui.lyric_windows.setWindowFlags(Qt.xx | Qt.yy)
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip(Tooltip)

        self._inner = InnerLyricWindow(self._app, self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._inner)

        self._old_pos = None

        esc_hide_widget(self)

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
            self._app.playlist.previous()
        elif e.button() == Qt.ForwardButton:
            self._app.playlist.next()

    def dump_state(self):
        inner = self._inner
        p = inner.palette()
        geo = self.geometry()
        return {
            'geometry': (geo.x(), geo.y(), geo.width(), geo.height()),
            'font': inner.font().toString(),
            'bg': p.color(QPalette.Active, QPalette.Window).name(QColor.HexArgb),
            'fg': p.color(QPalette.Active, QPalette.Text).name(QColor.HexArgb),
        }

    def apply_state(self, state):
        if not state:
            return

        inner = self._inner

        geo = state.get('geometry')
        if geo:
            self.resize(geo[2], geo[3])
            self.setGeometry(*geo)
        font = inner.font()
        font.fromString(state['font'])
        inner.setFont(font)
        palette = inner.palette()
        set_bg_color(palette, QColor(state['bg']))
        set_fg_color(palette, QColor(state['fg']))
        inner.setPalette(palette)

    def sizeHint(self):
        return QSize(500, 60)

    def resizeEvent(self, e):
        return super().resizeEvent(e)


class SentenceLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAlignment(Qt.AlignBaseline | Qt.AlignVCenter | Qt.AlignHCenter)
        self.setWordWrap(False)


class LineLabel(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.v_spacing = 10
        self.show_trans = True  # Show translated lyric or not.
        self.label = SentenceLabel(parent=self)
        self.trans_label = SentenceLabel(parent=self)
        self.spacer = QSpacerItem(0, 0)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(self.v_spacing // 2)
        self._layout.addWidget(self.label)
        self._layout.addSpacerItem(self.spacer)
        self._layout.addWidget(self.trans_label)
        self._layout.addSpacing(self.v_spacing // 2)

        line = LyricLine('...', '...', False)
        self.set_line(line)
        # The default size(calculated by Qt) may be different from the size
        # calculated by line_sizehint. Remember to specify size at very first,
        # otherwise it may show with the default size(calculated by Qt).
        self.resize(self.line_sizehint(line))

    def toggle_show_trans(self):
        self.show_trans = not self.show_trans
        if self.show_trans:
            self.trans_label.show()
            self.spacer.changeSize(0, self.v_spacing//3)
        else:
            self.trans_label.hide()
            self.spacer.changeSize(0, 0)

    def set_line(self, line: LyricLine):
        self.label.setText(
            elided_text(line.origin, self.width(), self.font()))
        if self.show_trans and line.has_trans:
            self.trans_label.show()
            self.trans_label.setText(
                elided_text(line.trans, self.width(), self.font()))
        else:
            self.trans_label.hide()

    def line_sizehint(self, line: LyricLine):
        """Proper size to show the line."""
        rect = self.label.fontMetrics().boundingRect(line.origin)
        height = rect.height()
        if self.show_trans and line.has_trans:
            height = height * 2
        # Sometimes width is not enough for text, so add buffer.
        h_buffer = rect.height()
        # Add some padding for vertical so that it looks more beautiful.
        v_buffer = rect.height() // 4
        height += self.v_spacing + v_buffer + self.spacer.geometry().height()
        return QSize(rect.width() + h_buffer, height)

    def setFont(self, font):
        super().setFont(font)

        self.label.setFont(font)
        font2 = QFont(font)
        font2.setBold(False)
        if font.pointSize() != 0:
            resize_font(font2, -4)
        else:
            resize_font(font2, -8)
        self.trans_label.setFont(font2)

    def setPalette(self, palette):
        super().setPalette(palette)
        self.label.setPalette(palette)
        self.trans_label.setPalette(palette)


class InnerLyricWindow(QWidget):
    """
    This window is responsible for rendering one line of a lyric.
    This window need not to know which song is playing, or if
    the song is changed.
    """

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._border_radius = 0
        # When _auto_resize is True,
        # the window size adapts to the lyric sentence width.
        self._auto_resize = True
        self._size_grip = SizeGrip(self)
        self.line_label = LineLabel(self)

        self._app.live_lyric.line_changed.connect(self.set_line)
        self._app.live_lyric.lyrics_changed.connect(self.on_lyrics_changed)
        QShortcut(QKeySequence.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.ZoomOut, self).activated.connect(self.zoomout)
        QShortcut(QKeySequence('Ctrl+='), self).activated.connect(self.zoomin)

        self._layout = QHBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        if self._auto_resize:
            self._size_grip.hide()
        self.on_font_size_changed()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.line_label)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignBottom)

    def set_line(self, line: LyricLine):
        # Ignore updating when the window is invisible.
        if not self.isVisible():
            return
        size = self.line_label.line_sizehint(line)
        self.line_label.resize(size)
        if self._auto_resize:
            self_size = QSize(size.width(), size.height())
            self.resize(self_size)
            self.parent().resize(self_size)  # type: ignore
            self.parent().updateGeometry()   # type: ignore
        self.line_label.set_line(line)

    def on_lyrics_changed(self, lyric, *_):
        if lyric is None:
            self.set_line(LyricLine('未找到可用歌词', '', False))

    def zoomin(self):
        font = self.font()
        resize_font(font, +1)
        self.setFont(font)

    def zoomout(self):
        font = self.font()
        resize_font(font, - 1)
        self.setFont(font)

    def on_font_size_changed(self):
        self._border_radius = self.fontMetrics().height() // 3
        width = max(1, self._border_radius * 2)
        self._size_grip.setFixedWidth(width)

    def paintEvent(self, e):
        """Draw shapes to make the size_grip more obvious.

        Note the shapes can't be drawed on the outside container (LyricWindow)
        due to it sets the attribute WA_TranslucentBackground.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)

        # Draw an circle button to indicate that the window can be resized.
        if self._auto_resize:
            return
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
        self.on_font_size_changed()

    def show_color_dialog(self, bg=True):
        def set_color(color):
            palette = self.palette()
            if bg:
                set_bg_color(palette, color)
            else:
                set_fg_color(palette, color)
            # Note that this widget(self) must also set the palette,
            # so the background can work as expected.
            self.setPalette(palette)

        dialog = QColorDialog(self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        if bg:
            color = self.palette().color(QPalette.Window)
        else:
            color = self.palette().color(QPalette.Text)
        dialog.setCurrentColor(color)
        dialog.currentColorChanged.connect(set_color)
        dialog.colorSelected.connect(set_color)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        # On KDE(with Xorg), if the dialog is in modal state,
        # the window is dimming.
        if sys.platform == 'linux':
            dialog.show()
        else:
            dialog.open()

    def show_font_dialog(self):
        dialog = QFontDialog(self.font(), self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.currentFontChanged.connect(self.setFont)
        dialog.fontSelected.connect(self.setFont)
        dialog.open()

    def toggle_auto_resize(self):
        self._auto_resize = not self._auto_resize
        if self._auto_resize:
            self._size_grip.hide()
        else:
            self._size_grip.show()

    def contextMenuEvent(self, e):
        menu = QMenu()
        bg_color_action = QAction('背景颜色', menu)
        fg_color_action = QAction('文字颜色', menu)
        font_action = QAction('字体', menu)
        toggle_trans_action = QAction('双语歌词', menu)
        toggle_trans_action.setCheckable(True)
        toggle_trans_action.setChecked(self.line_label.show_trans)
        toggle_fiexed_size_action = QAction('大小自动', menu)
        toggle_fiexed_size_action.setCheckable(True)
        toggle_fiexed_size_action.setChecked(self._auto_resize)
        menu.addAction(bg_color_action)
        menu.addAction(fg_color_action)
        menu.addSeparator()
        menu.addAction(font_action)
        menu.addSeparator()
        menu.addAction(toggle_trans_action)
        menu.addAction(toggle_fiexed_size_action)

        bg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=True))
        fg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=False))
        font_action.triggered.connect(self.show_font_dialog)
        toggle_trans_action.triggered.connect(self.line_label.toggle_show_trans)
        toggle_fiexed_size_action.triggered.connect(self.toggle_auto_resize)

        menu.exec(e.globalPos())

    def showEvent(self, e) -> None:
        self.set_line(self._app.live_lyric.current_line)
        return super().showEvent(e)
