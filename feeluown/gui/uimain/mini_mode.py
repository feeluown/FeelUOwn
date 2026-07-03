import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QEvent, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from feeluown.gui.components.dynamic_island import DynamicIslandStatusBar
from feeluown.gui.helpers import IS_MACOS
from feeluown.i18n import t

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class MiniModeWindow(QWidget):
    """Frameless standalone window for the dynamic island player status."""

    exit_requested = pyqtSignal()

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._drag_global_pos = None
        self._using_system_move = False

        if IS_MACOS:
            flags = (
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.FramelessWindowHint
            )
        else:
            flags = (
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.Tool
            )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.island = DynamicIslandStatusBar(app, parent=self)
        self.island.installEventFilter(self)
        for child in self.island.findChildren(QWidget):
            child.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.island)

        QShortcut(QKeySequence.StandardKey.Cancel, self).activated.connect(
            self.exit_requested.emit
        )

    def showEvent(self, event):
        self._resize_to_island()
        self.island.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        super().showEvent(event)

    def resizeEvent(self, event):
        self._resize_to_island()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self._show_context_menu(event.globalPos())
        event.accept()

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget) and event.type() == QEvent.Type.ContextMenu:
            self._show_context_menu(event.globalPos())
            return True
        if isinstance(obj, QWidget) and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
        ):
            return self._handle_drag_event(obj, event)
        elif obj is self.island and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.Hide,
        ):
            self._resize_to_island()
        return super().eventFilter(obj, event)

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        exit_action = menu.addAction(t("mini-mode-exit"))
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.exec(global_pos)

    def _handle_drag_event(self, obj, event):
        if self._is_interactive_drag_source(obj):
            self._drag_global_pos = None
            self._using_system_move = False
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._start_system_move():
                    self._using_system_move = True
                    self._drag_global_pos = None
                else:
                    self._drag_global_pos = event.globalPosition()
                return True
            return False

        if event.type() == QEvent.Type.MouseMove:
            if self._using_system_move:
                return True
            if self._drag_global_pos is None:
                return False
            delta = event.globalPosition() - self._drag_global_pos
            self.move(
                int(self.x() + delta.x()),
                int(self.y() + delta.y()),
            )
            self._drag_global_pos = event.globalPosition()
            return True

        if event.type() == QEvent.Type.MouseButtonRelease:
            had_drag = self._drag_global_pos is not None or self._using_system_move
            self._drag_global_pos = None
            self._using_system_move = False
            return had_drag

        return False

    def _start_system_move(self):
        handle = self.windowHandle()
        if handle is None:
            return False
        try:
            return bool(handle.startSystemMove())
        except RuntimeError:
            return False

    def _is_interactive_drag_source(self, obj):
        if isinstance(obj, (QAbstractButton, QAbstractSlider)):
            return True
        parent = obj.parent() if isinstance(obj, QWidget) else None
        while isinstance(parent, QWidget):
            if isinstance(parent, (QAbstractButton, QAbstractSlider)):
                return True
            parent = parent.parent()
        return False

    def _resize_to_island(self):
        self.setFixedSize(self.island.size())


class MiniModeManager(QObject):
    """Owns the mini-mode window and coordinates main-window visibility."""

    mode_changed = pyqtSignal(bool)

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._active = False
        self._restore_main_window = False
        self._window_was_placed = False
        self.window = MiniModeWindow(app)
        self.window.hide()
        self.window.exit_requested.connect(self.exit)

    @property
    def is_active(self):
        return self._active

    def enter(self):
        if self._active:
            self.window.show()
            self.window.raise_()
            return

        self._active = True
        self._restore_main_window = self._app.isVisible()
        self._place_window_if_needed()
        self.window.show()
        self.window.raise_()
        if self._restore_main_window:
            self._app.hide()
        self.mode_changed.emit(True)
        logger.debug("enter mini mode")

    def exit(self):
        if not self._active:
            self.window.hide()
            return

        self._active = False
        self.window.hide()
        if self._restore_main_window:
            self._app.show()
            self._app.activateWindow()
        self._restore_main_window = False
        self.mode_changed.emit(False)
        logger.debug("exit mini mode")

    def toggle(self):
        if self._active:
            self.exit()
        else:
            self.enter()

    def set_enabled(self, enabled):
        if enabled:
            self.enter()
        else:
            self.exit()

    def _place_window_if_needed(self):
        if self._window_was_placed:
            return

        self.window._resize_to_island()
        app_geo = self._app.geometry()
        width = max(1, self.window.width())
        x = app_geo.x() + (app_geo.width() - width) // 2
        y = app_geo.y() + 24
        self.window.move(QPoint(x, y))
        self._window_was_placed = True


if __name__ == "__main__":
    from feeluown.gui.debug import (
        create_mini_player_debug_app,
        simple_qapp,
        start_mini_player_debug_updates,
    )

    with simple_qapp():
        app = create_mini_player_debug_app()
        window = MiniModeWindow(app)
        window.exit_requested.connect(window.close)
        window.show()
        window.move(320, 160)
        start_mini_player_debug_updates(app, window)
