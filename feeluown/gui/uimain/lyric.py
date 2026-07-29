import sys

from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import (
    QPalette,
    QColor,
    QPainter,
    QKeySequence,
    QFont,
    QAction,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizeGrip,
    QHBoxLayout,
    QColorDialog,
    QMenu,
    QFontDialog,
)

from feeluown.i18n import t
from feeluown.gui.helpers import esc_hide_widget, resize_font
from feeluown.gui.components.desktop_lyric import DesktopLyricView


IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"


def set_bg_color(palette, color):
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, color)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, color)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, color)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, color)


def set_fg_color(palette, color):
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, color)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, color)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, color)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, color)


Tooltip = """
* Right-click can pop up the settings menu
* Ctrl+= or Ctrl++ can increase font size
* Ctrl+- can decrease font size
* Mouse forward/back buttons can play the previous/next track
* ESC key can close this lyrics window
"""


DEFAULT_HEIGHT_LINES = 3
HEIGHT_LINE_OPTIONS = (1, 3, 5, 7)


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
            flags = (
                Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
            )
        else:
            # TODO: use proper flags on other platforms, see #413 for more details.
            # User can customize the flags in the .fuorc or searchbox, like
            #    app.ui.lyric_windows.setWindowFlags(Qt.xx | Qt.yy)
            flags = (
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.Tool
            )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setToolTip(Tooltip)

        self._inner = InnerLyricWindow(self._app, self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._inner)

        self._old_pos = None
        self._using_system_move = False
        self._drag_started = False

        esc_hide_widget(self)

        # Install event filter on the lyric view's viewport so we can
        # detect mouse events for window dragging.  QListWidget consumes
        # mouse events via QAbstractItemView's internal filter, preventing
        # them from reaching LyricWindow's own mouse handlers.
        self._inner.lyric_view.viewport().installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj is self._inner.lyric_view.viewport():
            etype = e.type()
            if etype == QEvent.Type.MouseButtonPress:
                self._old_pos = e.globalPosition()
                self._drag_started = False
            elif etype == QEvent.Type.MouseMove:
                if self._old_pos is not None:
                    delta = e.globalPosition() - self._old_pos
                    if not self._drag_started and (delta.x() or delta.y()):
                        self._drag_started = True
                    self.move(
                        int(self.x() + delta.x()), int(self.y() + delta.y())
                    )
                    self._old_pos = e.globalPosition()
            elif etype == QEvent.Type.MouseButtonRelease:
                if not self._drag_started:
                    if e.button() == Qt.MouseButton.BackButton:
                        self._app.playlist.previous()
                        self._old_pos = None
                        return True
                    elif e.button() == Qt.MouseButton.ForwardButton:
                        self._app.playlist.next()
                        self._old_pos = None
                        return True
                self._old_pos = None
                self._drag_started = False
        return False

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        if self._start_system_move():
            self._using_system_move = True
            self._old_pos = None
        else:
            self._old_pos = e.globalPosition()
        e.accept()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.MouseButton.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._using_system_move:
            e.accept()
            return
        if self._old_pos is not None:
            delta = e.globalPosition() - self._old_pos
            self.move(int(self.x() + delta.x()), int(self.y() + delta.y()))
            self._old_pos = e.globalPosition()
            e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if self._old_pos is not None or self._using_system_move:
                self._old_pos = None
                self._using_system_move = False
                e.accept()
                return
        if not self.rect().contains(e.position().toPoint()):
            return
        if e.button() == Qt.MouseButton.BackButton:
            self._app.playlist.previous()
        elif e.button() == Qt.MouseButton.ForwardButton:
            self._app.playlist.next()

    def _start_system_move(self):
        handle = self.windowHandle()
        if handle is None:
            return False
        try:
            return bool(handle.startSystemMove())
        except RuntimeError:
            return False

    def dump_state(self):
        inner = self._inner
        p = inner.palette()
        geo = self.geometry()
        return {
            "geometry": (geo.x(), geo.y(), geo.width(), geo.height()),
            "font": inner.font().toString(),
            "bg": p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window).name(
                QColor.NameFormat.HexArgb
            ),
            "fg": p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text).name(
                QColor.NameFormat.HexArgb
            ),
            "height_lines": inner.height_lines,
            "auto_resize": inner.auto_resize,
        }

    def apply_state(self, state):
        if not state:
            return

        inner = self._inner

        # auto_resize defaults to True for backward compatibility with
        # state files saved before this field was added.
        auto_resize = state.get("auto_resize", True)
        height_lines = state.get("height_lines", DEFAULT_HEIGHT_LINES)

        inner._height_lines = max(1, int(height_lines))
        # For legacy states that had height_lines > 1 but no auto_resize
        # field, override to single-line mode.
        if auto_resize:
            inner._height_lines = 1
        inner._apply_mode_state()

        font = inner.font()
        font.fromString(state["font"])
        inner.setFont(font)
        palette = inner.palette()
        set_bg_color(palette, QColor(state["bg"]))
        set_fg_color(palette, QColor(state["fg"]))
        inner.setPalette(palette)

        geo = state.get("geometry")
        if geo:
            # Apply geometry last so the user-saved size overrides the
            # auto-sized height produced by setFont -> _apply_height_lines.
            self.resize(geo[2], geo[3])
            self.setGeometry(*geo)
        else:
            inner._apply_height_lines()

    def sizeHint(self):
        inner_hint = self._inner.sizeHint()
        return QSize(
            max(500, inner_hint.width()),
            max(60, inner_hint.height()),
        )


class InnerLyricWindow(QWidget):
    """
    Renders the inner content of the lyric window. It hosts a
    :class:`DesktopLyricView` which is responsible for the
    multi-line scrolling lyric rendering.
    """

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._border_radius = 0
        self._auto_resize = True
        self._height_lines = DEFAULT_HEIGHT_LINES
        self._size_grip = SizeGrip(self)
        self.lyric_view = DesktopLyricView(self._app, self)

        self._app.live_lyric.line_changed.connect(self._on_line_changed, weak=True)

        QShortcut(QKeySequence.StandardKey.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.StandardKey.ZoomOut, self).activated.connect(
            self.zoomout
        )
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self.zoomin)

        self._layout = QHBoxLayout(self)
        # Sync the inner's font with the view's font so Ctrl+/- operates
        # on the same font that drives the line metrics.
        self.setFont(self.lyric_view.font())
        self.setup_ui()

    @property
    def height_lines(self):
        return self._height_lines

    @property
    def auto_resize(self):
        return self._auto_resize

    def setup_ui(self):
        self._update_metrics()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.lyric_view)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignmentFlag.AlignBottom)
        if self._auto_resize:
            self._size_grip.hide()
        self._apply_height_lines()

    def set_height_lines(self, n, refresh=True):
        n = max(1, int(n))
        self._height_lines = n
        self._apply_mode_state()
        if refresh:
            self._apply_height_lines()

    def _apply_mode_state(self):
        if self._height_lines == 1:
            self._auto_resize = True
            self._size_grip.hide()
        else:
            self._auto_resize = False
            self._size_grip.show()

    def _on_line_changed(self, line):
        if not self.isVisible():
            return
        if self._auto_resize and line is not None:
            # In auto-resize mode, resize the window to fit the current
            # line text width (single-line behavior).
            rect = self.fontMetrics().boundingRect(line.origin)
            h_buffer = rect.height()
            width = rect.width() + h_buffer
            width = max(500, width)
            height = self._line_height_for_lines(1)
            self.resize(width, height)
            parent = self.parent()
            if parent is not None:
                parent.resize(width, height)
                parent.updateGeometry()

    def _line_height_for_lines(self, n):
        item_slot = max(1, self.lyric_view.item_slot_height())
        return item_slot * n + self._border_radius * 2

    def _apply_height_lines(self):
        n = 1 if self._auto_resize else self._height_lines
        new_height = self._line_height_for_lines(n)
        self.resize(self.width(), new_height)
        parent = self.parent()
        if parent is not None:
            parent.resize(parent.width(), new_height)
            parent.updateGeometry()

    def _update_metrics(self):
        self._border_radius = self.fontMetrics().height() // 3
        width = max(1, self._border_radius * 2)
        self._size_grip.setFixedWidth(width)

    def zoomin(self):
        font = self.font()
        resize_font(font, +1)
        self.setFont(font)

    def zoomout(self):
        font = self.font()
        resize_font(font, -1)
        self.setFont(font)

    def sizeHint(self):
        n = 1 if self._auto_resize else self._height_lines
        return QSize(
            500,
            self._line_height_for_lines(n),
        )

    def paintEvent(self, e):
        """Draw shapes to make the size_grip more obvious.

        Note the shapes can't be drawed on the outside container (LyricWindow)
        due to it sets the attribute WA_TranslucentBackground.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.palette().color(QPalette.ColorRole.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)

    def setPalette(self, a0: QPalette) -> None:
        super().setPalette(a0)
        self.lyric_view.setPalette(a0)

    def setFont(self, a0: QFont) -> None:
        super().setFont(a0)
        self.lyric_view.setFont(a0)
        self._update_metrics()
        self._apply_height_lines()

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
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if bg:
            color = self.palette().color(QPalette.ColorRole.Window)
        else:
            color = self.palette().color(QPalette.ColorRole.Text)
        dialog.setCurrentColor(color)
        dialog.currentColorChanged.connect(set_color)
        dialog.colorSelected.connect(set_color)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        # On KDE(with Xorg), if the dialog is in modal state,
        # the window is dimming.
        if sys.platform == "linux":
            dialog.show()
        else:
            dialog.open()

    def show_font_dialog(self):
        dialog = QFontDialog(self.font(), self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.currentFontChanged.connect(self.setFont)
        dialog.fontSelected.connect(self.setFont)
        dialog.open()

    def contextMenuEvent(self, e):
        menu = QMenu()
        bg_color_action = QAction(t("lyric-background-color"), menu)
        fg_color_action = QAction(t("lyric-text-color"), menu)
        font_action = QAction(t("lyric-font"), menu)

        menu.addAction(bg_color_action)
        menu.addAction(fg_color_action)
        menu.addSeparator()
        menu.addAction(font_action)
        menu.addSeparator()
        lines_menu = menu.addMenu(t("lyric-show-lines"))

        bg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=True))
        fg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=False))
        font_action.triggered.connect(self.show_font_dialog)

        for n in HEIGHT_LINE_OPTIONS:
            action = QAction(str(n), lines_menu)
            action.setCheckable(True)
            action.setChecked(
                (n == 1 and self._auto_resize)
                or (not self._auto_resize and self._height_lines == n)
            )
            action.triggered.connect(lambda checked, n=n: self.set_height_lines(n))
            lines_menu.addAction(action)

        menu.exec(e.globalPos())

    def showEvent(self, e) -> None:
        self.lyric_view.scroll_to_current()
        return super().showEvent(e)
