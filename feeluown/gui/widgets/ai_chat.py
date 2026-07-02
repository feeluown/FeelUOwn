import logging

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QPalette,
    QTextDocument,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from feeluown.i18n import t
from feeluown.gui.helpers import secondary_text_color
from feeluown.gui.widgets.textbtn import TextButton

logger = logging.getLogger(__name__)

SurfaceRadius = 8


def _application_palette():
    return QGuiApplication.palette()


def _set_text_color(widget, color: QColor):
    pal = widget.palette()
    pal.setColor(QPalette.ColorRole.WindowText, color)
    pal.setColor(QPalette.ColorRole.Text, color)
    widget.setPalette(pal)


def _set_bg_color(widget, color: QColor):
    pal = QPalette(_application_palette())
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        pal.setColor(group, QPalette.ColorRole.Window, color)
        pal.setColor(group, QPalette.ColorRole.Base, color)
    widget.setPalette(pal)


def draw_round_surface(
    widget,
    radius=SurfaceRadius,
    background_role=QPalette.ColorRole.Window,
):
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    rect = QRectF(widget.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
    path.addRoundedRect(rect, radius, radius)
    pal = widget.palette()
    painter.fillPath(path, pal.color(background_role))
    border_color = surface_border_color(pal, background_role)
    painter.setPen(border_color)
    painter.drawPath(path)
    painter.end()


def surface_border_color(palette, background_role=QPalette.ColorRole.Window):
    bg_color = palette.color(background_role)
    border_color = palette.color(QPalette.ColorRole.WindowText)
    border_color.setAlpha(72 if bg_color.lightness() < 128 else 52)
    return border_color


class ChatInputEditor(QPlainTextEdit):
    """Custom editor for chat input with Enter key handling"""

    enter_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setMinimumHeight(30)
        self.setMaximumHeight(300)  # TODO: set maximum height based on parent size
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()
        # The size policy matters
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QSize:  # noqa: D102
        font_metrics = self.fontMetrics()
        line_height = font_metrics.lineSpacing()
        doc = self.document()
        line_count = doc.lineCount()
        doc_height = line_count * line_height

        # Add some padding, 10
        new_height = min(
            max(int(doc_height) + 10, self.minimumHeight()), self.maximumHeight()
        )
        return QSize(super().sizeHint().width(), new_height)

    def adjust_height(self):
        self.updateGeometry()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and not event.modifiers():
            self.enter_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class ChatSendButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("ai-chat-send-button"))
        self.setText("")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pal = self.palette()
        bg_color = pal.color(QPalette.ColorRole.Highlight)
        arrow_color = pal.color(QPalette.ColorRole.HighlightedText)
        if not self.isEnabled():
            bg_color = pal.color(QPalette.ColorRole.Mid)
            arrow_color = pal.color(QPalette.ColorRole.Window)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))

        pen = QPen(arrow_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        center_x = self.width() / 2
        painter.drawLine(QPointF(center_x, 9), QPointF(center_x, 23))
        painter.drawLine(QPointF(center_x, 9), QPointF(center_x - 6, 15))
        painter.drawLine(QPointF(center_x, 9), QPointF(center_x + 6, 15))
        painter.end()


class RoundedLabel(QTextBrowser):
    link_activated = pyqtSignal(str)
    link_context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._radius = SurfaceRadius
        self._padding = 8
        self._surface_visible = True
        self.setReadOnly(True)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.document().setDocumentMargin(self._padding)
        self.document().contentsChanged.connect(self._update_height)
        self.anchorClicked.connect(lambda url: self.link_activated.emit(url.toString()))
        self.viewport().setAutoFillBackground(False)

    def setWordWrap(self, wrap):  # noqa: N802
        if wrap:
            self.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)

    def paintEvent(self, event):
        if self._surface_visible:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            rect = QRectF(self.viewport().rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            path.addRoundedRect(rect, self._radius, self._radius)
            painter.fillPath(path, self.palette().color(self.backgroundRole()))
            painter.setPen(surface_border_color(self.palette(), self.backgroundRole()))
            painter.drawPath(path)
            painter.end()
        super().paintEvent(event)

    def set_surface_visible(self, visible):
        self._surface_visible = visible
        self.update()

    def set_markdown(self, text):
        document = QTextDocument()
        document.setMarkdown(text)
        self.setHtml(document.toHtml())
        self._update_height()

    def setText(self, text):  # noqa: N802
        self.setPlainText(text)
        self._update_height()

    def text(self):
        return self.toHtml()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height()

    def contextMenuEvent(self, event):
        href = self.anchorAt(event.pos())
        if href:
            self.link_context_menu_requested.emit(href, event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def _update_height(self):
        width = max(1, self.viewport().width())
        self.document().setTextWidth(width)
        height = int(self.document().size().height()) + 2
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        self.updateGeometry()


class ChatMessageRow(QWidget):
    def __init__(self, role, label, parent=None):
        super().__init__(parent=parent)
        self.role = role
        self.label = label
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if role == "user":
            layout.addStretch(1)
            layout.addWidget(label, 0, Qt.AlignmentFlag.AlignRight)
        else:
            layout.addWidget(label)

        self.update_label_width()

    def update_label_width(self):
        if self.role == "user":
            available_width = max(1, self.width())
            max_width = min(available_width, max(240, int(available_width * 0.7)))
            self.label.setMaximumWidth(max_width)
        else:
            self.label.setMaximumWidth(16777215)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_label_width()


class ChatArtifactCard(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, artifact, parent=None):
        super().__init__(parent=parent)
        self.artifact = artifact
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFrameShape(QFrame.Shape.NoFrame)

        title_label = QLabel(artifact.title, self)
        title_label.setWordWrap(True)
        subtitle_label = QLabel(
            t("ai-chat-artifact-songs", count=len(artifact.songs)), self
        )
        self._subtitle_label = subtitle_label
        self._apply_palette()
        open_btn = TextButton(t("ai-chat-artifact-open"), height=24)
        open_btn.clicked.connect(lambda: self.clicked.emit(self.artifact))

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        layout.addLayout(text_layout, 1)
        layout.addWidget(open_btn)

    def _apply_palette(self):
        _set_text_color(
            self._subtitle_label,
            secondary_text_color(_application_palette()),
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path.addRoundedRect(rect, SurfaceRadius, SurfaceRadius)

        pal = self.palette()
        # Use Base for a slightly elevated card look
        card_bg = pal.color(QPalette.ColorRole.Base)
        painter.fillPath(path, card_bg)
        painter.setPen(surface_border_color(pal, QPalette.ColorRole.Base))
        painter.drawPath(path)
        painter.end()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.artifact)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ChatStreamingStatusCard(QFrame):
    def __init__(self, text="", parent=None):
        super().__init__(parent=parent)
        self._base_text = text
        self._dots = 0
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._label = QLabel(self)
        self._label.setWordWrap(False)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._apply_palette()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._advance)
        self._timer.start()
        self._update_text()

    def _apply_palette(self):
        pal = QPalette(_application_palette())
        surface_color = pal.color(QPalette.ColorRole.Window)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            pal.setColor(group, QPalette.ColorRole.Window, surface_color)
            pal.setColor(group, QPalette.ColorRole.Base, surface_color)
        self.setPalette(pal)
        _set_text_color(self._label, pal.color(QPalette.ColorRole.WindowText))
        self.update()

    def set_status(self, text):
        self._base_text = text
        self._dots = 0
        self._update_text()

    def text(self):
        return self._label.text()

    def finish(self, text=None):
        self._timer.stop()
        self._dots = 0
        if text is not None:
            self._base_text = text
        self._update_text()

    def paintEvent(self, event):
        draw_round_surface(
            self,
            SurfaceRadius,
            QPalette.ColorRole.Window,
        )
        super().paintEvent(event)

    def _advance(self):
        self._dots = (self._dots + 1) % 4
        self._update_text()

    def _update_text(self):
        self._label.setText(f"{self._base_text}{'.' * self._dots}")


class ChatToolEventCard(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._label = QLabel(text, self)
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._apply_palette()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self._label)

    def _apply_palette(self):
        _set_text_color(self._label, secondary_text_color(_application_palette()))
        self.update()

    def text(self):
        return self._label.text()


class ChatHistoryWidget(QWidget):
    """Widget for displaying chat history"""

    artifact_clicked = pyqtSignal(object)
    link_activated = pyqtSignal(str)
    link_context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._history_area = QScrollArea(self)
        self.history_widget = QWidget()
        self._history_area.setWidget(self.history_widget)
        self._history_layout = QVBoxLayout(self.history_widget)

        self._history_area.setFrameShape(QFrame.Shape.NoFrame)
        self._history_area.setAutoFillBackground(True)
        self._history_area.viewport().setAutoFillBackground(True)
        self.history_widget.setAutoFillBackground(True)
        self._apply_palette()
        self._history_layout.setContentsMargins(0, 0, 20, 0)
        self._history_layout.setSpacing(5)
        self._history_area.setWidgetResizable(True)
        # Adjust spacing between messages
        self._history_layout.setSpacing(10)
        self._history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._history_layout.addStretch(0)

        layout = QVBoxLayout(self)
        layout.addWidget(self._history_area)
        layout.setContentsMargins(0, 0, 0, 0)

    def _apply_palette(self):
        pal = _application_palette()
        bg_color = pal.color(QPalette.ColorRole.Base)
        self._set_bg_color(self._history_area, bg_color)
        self._set_bg_color(self._history_area.viewport(), bg_color)
        self._set_bg_color(self.history_widget, bg_color)
        for label in self.findChildren(RoundedLabel):
            row = label.parent()
            if isinstance(row, ChatMessageRow):
                self._apply_message_label_palette(label, row.role)
        for card in self.findChildren(ChatArtifactCard):
            card._apply_palette()
        for card in self.findChildren(ChatStreamingStatusCard):
            card._apply_palette()
        for card in self.findChildren(ChatToolEventCard):
            card._apply_palette()
        self._history_area.update()
        self._history_area.viewport().update()
        self.history_widget.update()

    def add_message(self, role, content):
        """Add a message to the history"""
        self.create_message_label(role, content)

    def add_artifact(self, artifact):
        card = ChatArtifactCard(artifact, self)
        card.clicked.connect(self.artifact_clicked.emit)
        self._history_layout.addWidget(card)
        self.scroll_to_bottom()
        return card

    def add_streaming_status(self, text):
        status = ChatStreamingStatusCard(text, self)
        self._history_layout.addWidget(status)
        self.scroll_to_bottom()
        return status

    def add_tool_event(self, text):
        event = ChatToolEventCard(text, self)
        self._history_layout.addWidget(event)
        self.scroll_to_bottom()
        return event

    def remove_history_widget(self, widget):
        widget = self._history_layout_widget(widget)
        self._history_layout.removeWidget(widget)
        widget.hide()
        widget.setParent(None)
        widget.deleteLater()
        self.scroll_to_bottom()

    def move_history_widget_to_bottom(self, widget):
        widget = self._history_layout_widget(widget)
        self._history_layout.removeWidget(widget)
        self._history_layout.addWidget(widget)
        self.scroll_to_bottom()

    def _history_layout_widget(self, widget):
        parent = widget.parent()
        if isinstance(parent, ChatMessageRow):
            return parent
        return widget

    def _set_bg_color(self, widget, color: QColor):
        _set_bg_color(widget, color)

    def _apply_message_label_palette(self, label, role):
        pal = QPalette(_application_palette())
        if role == "user":
            label.setBackgroundRole(QPalette.ColorRole.Window)
            bg_color = pal.color(QPalette.ColorRole.Window)
            pal.setColor(QPalette.ColorRole.Window, bg_color)
            pal.setColor(QPalette.ColorRole.Base, bg_color)
            label.setPalette(pal)
            label.update()
        elif role in ("assistant", "system"):
            label.setBackgroundRole(QPalette.ColorRole.Base)
            label.set_surface_visible(False)
            bg_color = pal.color(QPalette.ColorRole.Base)
            pal.setColor(QPalette.ColorRole.Window, bg_color)
            pal.setColor(QPalette.ColorRole.Base, bg_color)
            label.setPalette(pal)
            label.update()
        elif role in ("tools"):
            text_color = pal.color(QPalette.ColorRole.ToolTipText)
            bg_color = pal.color(QPalette.ColorRole.ToolTipBase)
            pal.setColor(QPalette.ColorRole.WindowText, text_color)
            pal.setColor(QPalette.ColorRole.Text, text_color)
            pal.setColor(QPalette.ColorRole.Window, bg_color)
            pal.setColor(QPalette.ColorRole.Base, bg_color)
            label.setPalette(pal)
            label.update()

    def create_message_label(self, role, content):
        """Create message label"""
        label = RoundedLabel()
        label.setWordWrap(True)
        label.setFrameStyle(QFrame.Shape.NoFrame)
        if role == "assistant":
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            label.set_markdown(content)
            label.link_activated.connect(self.link_activated.emit)
            label.link_context_menu_requested.connect(
                self.link_context_menu_requested.emit
            )
        else:
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setText(content)

        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        if role == "user":
            self._apply_message_label_palette(label, role)
        elif role in ("assistant", "system"):
            self._apply_message_label_palette(label, role)
        elif role in ("tools"):
            font = label.font()
            font.setPixelSize(11)
            font.setFamilies(["Monaco", "Menlo", "monospace"])
            label.setFont(font)
            self._apply_message_label_palette(label, role)

        row = ChatMessageRow(role, label, self)
        self._history_layout.addWidget(row)
        self.scroll_to_bottom()
        return label

    def scroll_to_bottom(self) -> None:
        """Scroll chat history to bottom."""
        self.history_widget.updateGeometry()
        self._history_area.verticalScrollBar().setValue(
            self._history_area.verticalScrollBar().maximum()
        )

    def clear(self):
        """Clear chat history"""
        while self._history_layout.count():
            item = self._history_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def widget(self):
        """Return the widget to be added to layouts"""
        return self


class ChatInputWidget(QWidget):
    """Widget for chat input and buttons"""

    send_clicked = pyqtSignal(str)  # emits query text

    def __init__(self, parent=None, status_widget=None):
        super().__init__(parent=parent)
        self._radius = SurfaceRadius
        self._editor = ChatInputEditor(self)
        self._editor.setPlaceholderText(t("ai-chat-input-placeholder"))
        self._editor.setFrameShape(QFrame.Shape.NoFrame)
        self._editor.setObjectName("ai_chat_input_editor")
        self._editor.setAutoFillBackground(False)
        self._editor.viewport().setAutoFillBackground(False)
        self._editor.setStyleSheet(
            """
            #ai_chat_input_editor {
                background: transparent;
                border: 0;
                padding: 0;
            }
            """
        )
        self._msg_label = QLabel(self)
        self._msg_label.setWordWrap(True)
        self._status_widget = status_widget
        if self._status_widget is not None:
            self._status_widget.setParent(self)
        self._send_btn = ChatSendButton(self)
        self._msg_level = "hint"
        self._updating_palette = False

        self._editor.enter_pressed.connect(self._on_enter_pressed)
        self._send_btn.clicked.connect(self._on_send_clicked)
        self._editor.setMinimumHeight(80)
        self.setAutoFillBackground(False)
        self._apply_palette()
        self.setup_ui()

    def _apply_editor_surface(self):
        pal = QPalette(_application_palette())
        editor_color = pal.color(QPalette.ColorRole.Window)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            pal.setColor(group, QPalette.ColorRole.Window, editor_color)
            pal.setColor(group, QPalette.ColorRole.Base, editor_color)
        self._editor.setPalette(pal)
        self._editor.viewport().setPalette(pal)

    def _apply_palette(self):
        if self._updating_palette:
            return
        self._updating_palette = True
        try:
            pal = QPalette(_application_palette())
            window_color = pal.color(QPalette.ColorRole.Window)
            pal.setColor(QPalette.ColorRole.Window, window_color)
            pal.setColor(QPalette.ColorRole.Base, window_color)
            self.setPalette(pal)
            self._apply_editor_surface()
            self._apply_msg_palette(self._msg_level)
            self.update()
        finally:
            self._updating_palette = False

    def _apply_msg_palette(self, level):
        if level == "hint":
            color = secondary_text_color(_application_palette())
        elif level == "warn":
            color = _application_palette().color(QPalette.ColorRole.ToolTipText)
        else:  # err
            color = _application_palette().color(QPalette.ColorRole.Highlight)
        _set_text_color(self._msg_label, color)

    def setup_ui(self):
        self._msg_label.setWordWrap(True)
        self._msg_label.setTextFormat(Qt.TextFormat.PlainText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 12, 6)
        layout.setSpacing(4)
        layout.addWidget(self._editor)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        if self._status_widget is not None:
            self._msg_label.hide()
            footer_layout.addWidget(
                self._status_widget,
                0,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )
            footer_layout.addStretch(1)
        else:
            footer_layout.addWidget(self._msg_label, 1)
        footer_layout.addWidget(self._send_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(footer_layout)

    def paintEvent(self, event):
        draw_round_surface(self, self._radius)
        super().paintEvent(event)

    def _on_enter_pressed(self):
        self._on_send_clicked()

    def _on_send_clicked(self):
        query = self._editor.toPlainText().strip()
        if query:
            self.send_clicked.emit(query)
            self._editor.clear()

    def set_msg(self, text, level="hint"):
        self._msg_level = level
        self._apply_msg_palette(level)
        self._msg_label.setText(text)
        if self._status_widget is None:
            self._msg_label.setVisible(bool(text))

    def clear_input(self):
        self._editor.clear()

    def get_input(self):
        return self._editor.toPlainText()

    def enable_send(self, enabled):
        self._send_btn.setEnabled(enabled)

    def set_placeholder(self, text):
        self._editor.setPlaceholderText(text)
