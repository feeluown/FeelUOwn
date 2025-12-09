import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPainterPath, QTextOption
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from feeluown.gui.helpers import palette_set_bg_color
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.header import MidHeader

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


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


class RoundedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._radius = 8
        self._padding = 8
        self.setContentsMargins(
            self._padding, self._padding, self._padding, self._padding
        )
        self.setWordWrap(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        # Fill background
        painter.fillPath(path, self.palette().color(self.backgroundRole()))
        super().paintEvent(event)


class ChatHistoryWidget(QWidget):
    """Widget for displaying chat history"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._history_area = QScrollArea(self)
        self._history_widget = QWidget()
        self._history_area.setWidget(self._history_widget)
        self._history_layout = QVBoxLayout(self._history_widget)

        self._history_area.setFrameShape(QFrame.Shape.NoFrame)
        self._history_area.setAutoFillBackground(True)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(5)
        self._history_area.setWidgetResizable(True)
        # Adjust spacing between messages
        self._history_layout.setSpacing(10)

        layout = QVBoxLayout(self)
        layout.addWidget(self._history_area)
        layout.setContentsMargins(0, 0, 0, 0)

    def add_message(self, role, content):
        """Add a message to the history"""
        label = self.create_message_label(role, content)
        self._history_layout.addWidget(label)
        self.scroll_to_bottom()

    def create_message_label(self, role, content):
        """Create message label"""
        label = RoundedLabel()
        label.setText(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setFrameStyle(QFrame.Shape.NoFrame)

        width_factor = 0.6 if role in ("user", "system") else 1
        label.setMaximumWidth(int(self._history_area.width() * width_factor))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        pal = label.palette()
        if role in ("user", "system"):
            origin_window = pal.color(pal.ColorRole.Window)
            palette_set_bg_color(pal, pal.color(pal.ColorRole.Highlight))
            pal.setColor(pal.ColorRole.Text, pal.color(pal.ColorRole.HighlightedText))
            pal.setColor(pal.ColorRole.Highlight, origin_window)
            label.setPalette(pal)

        return label

    def scroll_to_bottom(self) -> None:
        """Scroll chat history to bottom."""
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

    def add_widget(self, widget):
        """Add a custom widget to the history layout"""
        self._history_layout.addWidget(widget)

    def widget(self):
        """Return the widget to be added to layouts"""
        return self


class ChatInputWidget(QWidget):
    """Widget for chat input and buttons"""

    send_clicked = pyqtSignal(str)  # emits query text
    clear_history_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._editor = ChatInputEditor(self)
        self._editor.setPlaceholderText("在这里输入你的问题...")
        self._editor.setFrameShape(QFrame.Shape.NoFrame)
        self._msg_label = QLabel(self)
        self._msg_label.setWordWrap(True)
        self._send_btn = TextButton("发送（回车）", self)
        self._clear_history_btn = TextButton("清空对话", self)

        self._editor.enter_pressed.connect(self._on_enter_pressed)
        self._send_btn.clicked.connect(self._on_send_clicked)
        self._clear_history_btn.clicked.connect(self.clear_history_clicked.emit)

        self.setup_ui()

    def setup_ui(self):
        self._msg_label.setWordWrap(True)
        self._msg_label.setTextFormat(Qt.TextFormat.RichText)

        layout = QVBoxLayout(self)
        layout.addWidget(self._msg_label)
        layout.addWidget(self._editor)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._clear_history_btn)
        btn_layout.addStretch(0)
        btn_layout.addWidget(self._send_btn)
        layout.addLayout(btn_layout)

    def _on_enter_pressed(self):
        self._on_send_clicked()

    def _on_send_clicked(self):
        query = self._editor.toPlainText().strip()
        if query:
            self.send_clicked.emit(query)

    def set_msg(self, text, level="hint"):
        if level == "hint":
            color = "green"
        elif level == "warn":
            color = "yellow"
        else:  # err
            color = "magenta"
        self._msg_label.setText(f'<span style="color: {color}">{text}</span>')

    def clear_input(self):
        self._editor.clear()

    def get_input(self):
        return self._editor.toPlainText()


class AIChatBox(QWidget):
    """
    A lightweight AI chat UI for the AI Radio page.
    This only provides UI; real message sending is intentionally left empty.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._header = MidHeader("AI 对话")
        self._history_widget = ChatHistoryWidget(self)
        self._input_widget = ChatInputWidget(self)
        self._input_widget.set_msg("当前未接入 AI，消息不会发送。")

        self._input_widget.send_clicked.connect(self._on_send_clicked)
        self._input_widget.clear_history_clicked.connect(self._history_widget.clear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._header)
        layout.addWidget(self._history_widget)
        layout.addWidget(self._input_widget)

    def _on_send_clicked(self, query: str):
        if not query:
            self._input_widget.set_msg("请输入内容后再发送", level="warn")
            return
        # Echo user message to history; no real AI request.
        self._history_widget.add_message("user", query)
        self._input_widget.set_msg("当前未接入 AI，未发送。", level="warn")
        self._input_widget.clear_input()
        # Optionally show a stub assistant reply
        self._history_widget.add_message("assistant", "（演示）这里将显示 AI 回复。")



if __name__ == "__main__":
    from PyQt6.QtCore import QSize
    from feeluown.gui.debug import mock_app, simple_layout

    with simple_layout(theme="dark") as layout, mock_app() as app:
        chat_box = AIChatBox()
        layout.addWidget(chat_box)
