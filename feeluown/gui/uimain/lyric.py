import sys

from PyQt6.QtCore import QEvent, Qt, QRectF, QRect, QSize
from PyQt6.QtGui import (
    QPalette,
    QColor,
    QTextOption,
    QPainter,
    QKeySequence,
    QFont,
    QAction,
    QActionGroup,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QSizeGrip,
    QHBoxLayout,
    QColorDialog,
    QMenu,
    QFontDialog,
    QSpacerItem,
    QAbstractButton,
    QAbstractSlider,
    QAbstractItemView,
)

from feeluown.i18n import t
from feeluown.gui.helpers import esc_hide_widget, resize_font, elided_text
from feeluown.player import LyricLine


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
        self._display_mode = "classic"
        self._classic_size = QSize(500, 60)
        self._multiline_size = QSize(500, 360)
        self.island = None
        self._mini_container = None
        self._multiline_view = None
        self._multiline_container = None

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
        # Native dragging also leaves _old_pos unset. Track it separately so
        # the event filter still consumes drag events from child widgets.
        self._using_system_move = False

        esc_hide_widget(self)

    @property
    def display_mode(self):
        return self._display_mode

    def set_display_mode(self, mode):
        if mode not in ("classic", "mini", "multiline"):
            raise ValueError(f"Unknown lyric display mode: {mode}")
        if mode == self._display_mode:
            return

        pos = self.pos()
        if self._display_mode == "classic":
            self._classic_size = self.size()
        elif self._display_mode == "multiline":
            self._multiline_size = self.size()
        self._old_pos = None
        self._using_system_move = False
        self._inner.hide()
        if self._mini_container is not None:
            self._mini_container.hide()
        if self._multiline_container is not None:
            self._multiline_container.hide()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self._display_mode = mode
        if mode == "mini":
            self._ensure_mini_view()
            self._mini_container.show()
            self._resize_to_island()
            self.island.setFocus(Qt.FocusReason.OtherFocusReason)
        elif mode == "multiline":
            self._ensure_multiline_view()
            self.setMinimumSize(240, 180)
            self.resize(self._multiline_size)
            self._multiline_container.show()
            self._multiline_view.on_line_changed(None)
        else:
            self.resize(self._classic_size)
            self._inner.show()
        self.move(pos)

    def _ensure_multiline_view(self):
        if self._multiline_view is not None:
            return
        from feeluown.gui.components.desktop_lyric import DesktopLyricCard

        self._multiline_container = DesktopLyricCard(self._app, self)
        self._multiline_drag_area = self._multiline_container.drag_area
        self._multiline_view = self._multiline_container.lyric_view
        self._multiline_grip = self._multiline_container.size_grip
        self._layout.addWidget(self._multiline_container)
        for widget in (
            self._multiline_container, self._multiline_drag_area,
            self._multiline_view, self._multiline_view.viewport(),
        ):
            widget.installEventFilter(self)

    def _ensure_mini_view(self):
        if self.island is not None:
            return
        from feeluown.gui.components.dynamic_island import DynamicIslandStatusBar

        # The island controls its own visibility on playback updates. A separate
        # container keeps these updates from exposing it in classic mode.
        self._mini_container = QWidget(self)
        self._mini_container.hide()
        layout = QVBoxLayout(self._mini_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.island = DynamicIslandStatusBar(
            self._app, parent=self._mini_container, hide_when_inactive=False
        )
        layout.addWidget(self.island)
        self._layout.addWidget(self._mini_container)
        self.island.installEventFilter(self)
        for child in self.island.findChildren(QWidget):
            if isinstance(child, (QAbstractButton, QAbstractSlider)):
                # Some controls ignore mouse presses, which would otherwise
                # bubble to the island and start a window drag.
                child.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)
            child.installEventFilter(self)

    def _resize_to_island(self):
        if self.display_mode == "mini" and self.island is not None:
            self._mini_container.setFixedSize(self.island.size())
            self.setFixedSize(self.island.size())

    def _create_context_menu(self):
        menu = QMenu(self)
        modes = menu.addMenu(t("lyric-display-mode"))
        group = QActionGroup(modes)
        group.setExclusive(True)
        for mode in ("classic", "mini", "multiline"):
            action = modes.addAction(t(f"lyric-mode-{mode}"))
            action.setData(mode)
            action.setCheckable(True)
            action.setChecked(mode == self.display_mode)
            group.addAction(action)
            action.triggered.connect(
                lambda checked, mode=mode: self.set_display_mode(mode)
            )
        menu.addSeparator()
        if self.display_mode == "classic":
            self._inner.add_settings_actions(menu)
            menu.addSeparator()
        menu.addAction(t("lyric-hide"), self.hide)
        return menu

    def _show_context_menu(self, global_pos):
        menu = self._create_context_menu()
        menu.exec(global_pos)
        menu.deleteLater()

    def contextMenuEvent(self, event):
        self._show_context_menu(event.globalPos())
        event.accept()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ContextMenu:
            self._show_context_menu(event.globalPos())
            return True
        if event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
        ):
            return self._handle_drag_event(obj, event)
        if obj is self.island and event.type() in (
            QEvent.Type.Resize, QEvent.Type.Show,
        ):
            self._resize_to_island()
        return super().eventFilter(obj, event)

    def _handle_drag_event(self, obj, event):
        parent = obj
        while isinstance(parent, QWidget) and parent is not self:
            if isinstance(parent, (
                QAbstractButton, QAbstractSlider, QAbstractItemView, QSizeGrip,
            )):
                return False
            parent = parent.parent()
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            self.mousePressEvent(event)
            return True
        if event.type() == QEvent.Type.MouseMove:
            dragging = self._old_pos is not None or self._using_system_move
            self.mouseMoveEvent(event)
            return dragging
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                dragging = self._old_pos is not None or self._using_system_move
                self.mouseReleaseEvent(event)
                return dragging
        return False

    def showEvent(self, event):
        if self.display_mode == "mini":
            self._resize_to_island()
            self.island.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        elif self.display_mode == "multiline":
            self._multiline_view.on_line_changed(None)
        super().showEvent(event)

    def hideEvent(self, event):
        self._old_pos = None
        self._using_system_move = False
        super().hideEvent(event)

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
        size = self.size() if self.display_mode == "classic" else self._classic_size
        multiline_size = (
            self.size() if self.display_mode == "multiline" else self._multiline_size
        )
        return {
            "display_mode": self.display_mode,
            "geometry": (geo.x(), geo.y(), size.width(), size.height()),
            "multiline_size": (multiline_size.width(), multiline_size.height()),
            "font": inner.font().toString(),
            "bg": p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window).name(
                QColor.NameFormat.HexArgb
            ),
            "fg": p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text).name(
                QColor.NameFormat.HexArgb
            ),
        }

    def apply_state(self, state):
        if not state:
            return

        inner = self._inner

        self.set_display_mode("classic")
        geo = state.get("geometry")
        if geo:
            self.setGeometry(*geo)
            self._classic_size = self.size()
        font = inner.font()
        font.fromString(state["font"])
        inner.setFont(font)
        palette = inner.palette()
        set_bg_color(palette, QColor(state["bg"]))
        set_fg_color(palette, QColor(state["fg"]))
        inner.setPalette(palette)
        self._multiline_size = QSize(*state.get("multiline_size", (500, 360)))
        self.set_display_mode(state.get("display_mode", "classic"))

    def sizeHint(self):
        return QSize(500, 60)


class SentenceLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAlignment(
            Qt.AlignmentFlag.AlignBaseline
            | Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignHCenter
        )
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

        line = LyricLine("...", "...", False)
        self.set_line(line)
        # The default size(calculated by Qt) may be different from the size
        # calculated by line_sizehint. Remember to specify size at very first,
        # otherwise it may show with the default size(calculated by Qt).
        self.resize(self.line_sizehint(line))

    def toggle_show_trans(self):
        self.show_trans = not self.show_trans
        if self.show_trans:
            self.trans_label.show()
            self.spacer.changeSize(0, self.v_spacing // 3)
        else:
            self.trans_label.hide()
            self.spacer.changeSize(0, 0)

    def set_line(self, line: LyricLine):
        self.label.setText(elided_text(line.origin, self.width(), self.font()))
        if self.show_trans and line.has_trans:
            self.trans_label.show()
            self.trans_label.setText(elided_text(line.trans, self.width(), self.font()))
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
        QShortcut(QKeySequence.StandardKey.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.StandardKey.ZoomOut, self).activated.connect(
            self.zoomout
        )
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self.zoomin)

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
        self._layout.setAlignment(self._size_grip, Qt.AlignmentFlag.AlignBottom)

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
            self.parent().updateGeometry()  # type: ignore
        self.line_label.set_line(line)

    def on_lyrics_changed(self, lyric, *_):
        if lyric is None:
            self.set_line(LyricLine(t("lyric-not-available"), "", False))

    def zoomin(self):
        font = self.font()
        resize_font(font, +1)
        self.setFont(font)

    def zoomout(self):
        font = self.font()
        resize_font(font, -1)
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.palette().color(QPalette.ColorRole.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)

        # Draw an circle button to indicate that the window can be resized.
        if self._auto_resize:
            return
        painter.save()
        painter.setPen(QColor("white"))
        option = QTextOption()
        option.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        rect = QRect(self.mapToParent(self._size_grip.pos()), self._size_grip.size())
        painter.drawText(QRectF(rect), "●", option)
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

    def toggle_auto_resize(self):
        self._auto_resize = not self._auto_resize
        if self._auto_resize:
            self._size_grip.hide()
        else:
            self._size_grip.show()

    def contextMenuEvent(self, e):
        self.parent().contextMenuEvent(e)

    def add_settings_actions(self, menu):
        bg_color_action = QAction(t("lyric-background-color"), menu)
        fg_color_action = QAction(t("lyric-text-color"), menu)
        font_action = QAction(t("lyric-font"), menu)
        toggle_trans_action = QAction(t("lyric-show-bilingual"), menu)
        toggle_trans_action.setCheckable(True)
        toggle_trans_action.setChecked(self.line_label.show_trans)
        toggle_fiexed_size_action = QAction(t("lyric-window-auto-resize"), menu)
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

    def showEvent(self, e) -> None:
        self.set_line(self._app.live_lyric.current_line)
        return super().showEvent(e)


if __name__ == "__main__":
    from feeluown.gui.debug import (
        create_mini_player_debug_app,
        simple_qapp,
        start_mini_player_debug_updates,
    )

    with simple_qapp():
        app = create_mini_player_debug_app()
        window = LyricWindow(app)
        window.show()
        window.move(320, 160)
        start_mini_player_debug_updates(app, window)
