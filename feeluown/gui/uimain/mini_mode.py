import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QEvent, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QFrame,
    QMenu,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from feeluown.gui.components.dynamic_island import DynamicIslandStatusBar
from feeluown.gui.helpers import IS_MACOS
from feeluown.gui.uimain.ai_chat import AIChatBox
from feeluown.gui.widgets.ai_chat import draw_round_surface
from feeluown.gui.widgets.selfpaint_btn import AIIconButton
from feeluown.i18n import t

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)

MINI_CHAT_DEFAULT_WIDTH = 340
MINI_CHAT_MIN_WIDTH = 280
RESIZE_MARGIN = 8


class MiniAIChatPanel(QFrame):
    """Compact AI chat panel used inside mini mode."""

    collapse_requested = pyqtSignal()

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.setMinimumWidth(MINI_CHAT_MIN_WIDTH)
        self.setAutoFillBackground(False)

        self._ai_btn = AIIconButton(
            length=24,
            padding=0.22,
            colorful=True,
            parent=self,
        )
        self._ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ai_btn.clicked.connect(self.collapse_requested.emit)
        self.island = DynamicIslandStatusBar(
            app,
            parent=self,
            trailing_widget=self._ai_btn,
        )
        self.chat_box = AIChatBox(
            app,
            self,
            status_widget=self.island,
            history_fixed_height=160,
            input_editor_min_height=34,
            input_editor_max_height=76,
            input_contents_margins=(10, 8, 8, 5),
            placeholder_text=t("mini-ai-chat-input-placeholder"),
        )
        self.history_widget = self.chat_box.history_widget
        self.input_widget = self.chat_box.input_widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.chat_box, 1)

    def focus_input(self):
        self.input_widget.focus_editor()

    async def exec_user_query(self, query: str):
        await self.chat_box.exec_user_query(query)

    def paintEvent(self, event):
        draw_round_surface(self)
        super().paintEvent(event)


class MiniModeWindow(QWidget):
    """Frameless standalone window for the dynamic island player status."""

    exit_requested = pyqtSignal()

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._drag_global_pos = None
        self._using_system_move = False
        self._resize_global_pos = None
        self._resize_start_geometry = None
        self._resize_edges = None
        self._using_system_resize = False
        self._chat_width = None
        self._chat_mode = False
        self._resizing_to_content = False

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

        self._ai_btn = AIIconButton(
            length=24,
            padding=0.22,
            colorful=True,
            parent=self,
        )
        self._ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chat_panel = None
        if self._app.ai is None:
            self._ai_btn.setDisabled(True)
            self._ai_btn.setToolTip(t("ai-configure-tooltip"))
        else:
            self._ai_btn.clicked.connect(self._toggle_ai_chat_panel)
        self.island = DynamicIslandStatusBar(
            app,
            parent=self,
            trailing_widget=self._ai_btn,
        )
        self._install_event_filters(self.island)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.island, 0, Qt.AlignmentFlag.AlignHCenter)

        QShortcut(QKeySequence.StandardKey.Cancel, self).activated.connect(
            self._on_cancel_requested
        )

    def showEvent(self, event):
        self._resize_to_content()
        self.island.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        super().showEvent(event)

    def resizeEvent(self, event):
        self._resize_to_content()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if self._handle_resize_event(self, event):
            event.accept()
            return
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_resize_event(self, event):
            event.accept()
            return
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._handle_resize_event(self, event):
            event.accept()
            return
        if self._handle_drag_event(self, event):
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self._show_context_menu(event.globalPos())
        event.accept()

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget) and event.type() == QEvent.Type.ContextMenu:
            if self._is_chat_panel_child(obj):
                return False
            self._show_context_menu(event.globalPos())
            return True
        if isinstance(obj, QWidget) and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
        ):
            if self._handle_resize_event(obj, event):
                return True
            return self._handle_drag_event(obj, event)
        elif obj is self.island and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.Hide,
        ):
            self._resize_to_content()
        return super().eventFilter(obj, event)

    def _toggle_ai_chat_panel(self):
        if self._chat_mode:
            self._hide_ai_chat_panel()
        else:
            self._show_ai_chat_panel()

    def _show_ai_chat_panel(self):
        self._chat_mode = True
        if self._chat_panel is None:
            self._chat_panel = MiniAIChatPanel(self._app, self)
            self._chat_panel.collapse_requested.connect(self._hide_ai_chat_panel)
            self._install_event_filters(self._chat_panel)
            self.layout().addWidget(
                self._chat_panel,
                0,
            )
        self.island.set_visibility_suppressed(True)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self._chat_panel.show()
        self._chat_panel.focus_input()
        if self._chat_width is None:
            self._chat_width = max(MINI_CHAT_DEFAULT_WIDTH, self.width())
        self.resize(self._chat_width, self.height())
        self._resize_to_content()

    def _hide_ai_chat_panel(self):
        self._chat_mode = False
        if self._chat_panel is not None:
            self._chat_width = self.width()
            self._chat_panel.hide()
        self.island.set_visibility_suppressed(False)
        self._resize_to_content()
        self.island.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _on_cancel_requested(self):
        if self._chat_mode:
            self._hide_ai_chat_panel()
        else:
            self.exit_requested.emit()

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        exit_action = menu.addAction(t("mini-mode-exit"))
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.exec(global_pos)

    def _handle_drag_event(self, obj, event):
        drag_active = (
            self._drag_global_pos is not None or self._using_system_move
        )
        if self._is_interactive_drag_source(obj) and not (
            drag_active
            or (
                self.isVisible()
                and self._is_window_side(event.globalPosition().toPoint())
            )
        ):
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

    def _handle_resize_event(self, _obj, event):
        if not self._chat_mode_active():
            return False

        global_pos = event.globalPosition().toPoint()
        if event.type() == QEvent.Type.MouseMove:
            if self._using_system_resize:
                return True
            if self._resize_start_geometry is not None:
                self._resize_manually(global_pos)
                return True
            edges = self._resize_edges_at(global_pos)
            if edges is not None:
                self.setCursor(self._resize_cursor(edges))
            else:
                self.unsetCursor()
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            edges = self._resize_edges_at(global_pos)
            if edges is None:
                return False
            if self._start_system_resize(edges):
                self._using_system_resize = True
            else:
                self._resize_global_pos = global_pos
                self._resize_start_geometry = self.frameGeometry()
                self._resize_edges = edges
            return True

        if event.type() == QEvent.Type.MouseButtonRelease:
            if self._using_system_resize or self._resize_start_geometry is not None:
                self._using_system_resize = False
                self._resize_global_pos = None
                self._resize_start_geometry = None
                self._resize_edges = None
                return True
        return False

    def _resize_edges_at(self, global_pos):
        geometry = self.frameGeometry()
        left = global_pos.x() <= geometry.left() + RESIZE_MARGIN
        right = global_pos.x() >= geometry.right() - RESIZE_MARGIN
        top = global_pos.y() <= geometry.top() + RESIZE_MARGIN
        bottom = global_pos.y() >= geometry.bottom() - RESIZE_MARGIN
        if left and top:
            return Qt.Edge.LeftEdge | Qt.Edge.TopEdge
        if right and top:
            return Qt.Edge.RightEdge | Qt.Edge.TopEdge
        if left and bottom:
            return Qt.Edge.LeftEdge | Qt.Edge.BottomEdge
        if right and bottom:
            return Qt.Edge.RightEdge | Qt.Edge.BottomEdge
        return None

    def _resize_cursor(self, edges):
        if edges in (
            Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
            Qt.Edge.RightEdge | Qt.Edge.BottomEdge,
        ):
            return Qt.CursorShape.SizeFDiagCursor
        return Qt.CursorShape.SizeBDiagCursor

    def _is_window_side(self, global_pos):
        geometry = self.frameGeometry()
        return (
            global_pos.x() <= geometry.left() + RESIZE_MARGIN
            or global_pos.x() >= geometry.right() - RESIZE_MARGIN
            or global_pos.y() <= geometry.top() + RESIZE_MARGIN
            or global_pos.y() >= geometry.bottom() - RESIZE_MARGIN
        )

    def _resize_manually(self, global_pos):
        start_geometry = self._resize_start_geometry
        start_pos = self._resize_global_pos
        if start_geometry is None or start_pos is None:
            return

        delta_x = global_pos.x() - start_pos.x()
        width = start_geometry.width()
        height = start_geometry.height()
        if self._resize_edges & Qt.Edge.LeftEdge:
            width -= delta_x
        elif self._resize_edges & Qt.Edge.RightEdge:
            width += delta_x
        if self._resize_edges & Qt.Edge.TopEdge:
            height -= global_pos.y() - start_pos.y()
        elif self._resize_edges & Qt.Edge.BottomEdge:
            height += global_pos.y() - start_pos.y()

        width = max(self.minimumWidth(), width)
        if self.maximumWidth() < 16777215:
            width = min(self.maximumWidth(), width)
        height = max(self.minimumHeight(), height)
        if self.maximumHeight() < 16777215:
            height = min(self.maximumHeight(), height)
        if self._resize_edges & Qt.Edge.LeftEdge:
            x = start_geometry.right() - width + 1
        else:
            x = start_geometry.x()
        if self._resize_edges & Qt.Edge.TopEdge:
            y = start_geometry.bottom() - height + 1
        else:
            y = start_geometry.y()
        self.setGeometry(x, y, width, height)

    def _start_system_move(self):
        handle = self.windowHandle()
        if handle is None:
            return False
        try:
            return bool(handle.startSystemMove())
        except RuntimeError:
            return False

    def _start_system_resize(self, edges):
        handle = self.windowHandle()
        if handle is None:
            return False
        try:
            return bool(handle.startSystemResize(edges))
        except RuntimeError:
            return False

    def _is_interactive_drag_source(self, obj):
        if self._is_chat_panel_child(obj):
            return True
        if isinstance(
            obj,
            (
                QAbstractButton,
                QAbstractSlider,
                QPlainTextEdit,
                QTextBrowser,
                QTextEdit,
                QScrollArea,
            ),
        ):
            return True
        parent = obj.parent() if isinstance(obj, QWidget) else None
        while isinstance(parent, QWidget):
            if isinstance(
                parent,
                (
                    QAbstractButton,
                    QAbstractSlider,
                    QPlainTextEdit,
                    QTextBrowser,
                    QTextEdit,
                    QScrollArea,
                ),
            ):
                return True
            parent = parent.parent()
        return False

    def _install_event_filters(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def _is_chat_panel_child(self, obj):
        panel = self._chat_panel
        if panel is None or not isinstance(obj, QWidget):
            return False
        if obj is panel:
            return True
        parent = obj.parent()
        while isinstance(parent, QWidget):
            if parent is panel:
                return True
            parent = parent.parent()
        return False

    def _resize_to_content(self):
        if (
            self._resizing_to_content
            or self._using_system_resize
            or self._resize_start_geometry is not None
        ):
            return
        self._resizing_to_content = True
        try:
            self.layout().activate()
            size = self.sizeHint()
            if not size.isValid():
                return
            if self._chat_mode_active():
                if self.height() != size.height():
                    self.resize(self.width(), size.height())
            elif self.size() != size:
                self.setFixedSize(size)
        finally:
            self._resizing_to_content = False

    def _chat_mode_active(self):
        return self._chat_mode

    def _resize_to_island(self):
        self._resize_to_content()


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
