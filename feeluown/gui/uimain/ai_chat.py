import asyncio
import logging
import time
from typing import List

from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QPalette, QResizeEvent, QFontMetrics
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from feeluown.ai import AISongModel, AISongMatcher
from feeluown.app.gui_app import GuiApp
from feeluown.gui.consts import ScrollBarWidth
from feeluown.gui.widgets import PlayButton, PlusButton
from feeluown.gui.widgets.header import MidHeader
from feeluown.gui.widgets.ai_chat import ChatHistoryWidget, ChatInputWidget
from feeluown.gui.components.overlay import AppOverlayContainer
from feeluown.utils import aio

logger = logging.getLogger(__name__)


class AISongItemWidget(QWidget):
    """Display a single AISongModel with play support."""

    def __init__(self, app: "GuiApp", ai_song: AISongModel, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._ai_song = ai_song
        self._matched_song = None
        self._match_lock = asyncio.Lock()

        self._title_label = QLabel(f"{ai_song.title} • {ai_song.artists_name}")
        self._desc_label = QLabel(ai_song.description)
        self._desc_label.setWordWrap(True)
        self._play_btn = PlayButton(length=16, padding=0.22)
        self._add_to_playlist_btn = PlusButton(length=16, padding=0.25)
        self._btns = [self._play_btn, self._add_to_playlist_btn]

        self._play_btn.clicked.connect(self._on_play_clicked)
        self._add_to_playlist_btn.clicked.connect(self._on_add_to_playlist_clicked)

        self._setup_ui()

    def _setup_ui(self):
        font = self._desc_label.font()
        font.setPixelSize(11)
        self._desc_label.setFont(font)
        palette = self._desc_label.palette()
        palette.setColor(
            QPalette.ColorRole.Text,
            palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text),
        )
        self._desc_label.setPalette(palette)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, ScrollBarWidth + 5, 5)
        layout.setSpacing(5)

        self.label_layout = label_layout = QVBoxLayout()
        label_layout.addWidget(self._title_label)
        label_layout.addWidget(self._desc_label)
        label_layout.addStretch(0)

        self.btn_layout = btn_layout = QHBoxLayout()
        btn_layout.setSpacing(0)
        for btn in self._btns:
            btn_layout.addWidget(btn)

        layout.addLayout(label_layout)
        layout.addLayout(btn_layout)

    def height_for_width(self, width) -> QSize:
        desc_fm = QFontMetrics(self._desc_label.font())
        h_spacing = (self.layout().spacing() +
                     self.btn_layout.spacing() * (len(self._btns) - 1))
        v_spacing = self.layout().spacing()
        margins = self.layout().contentsMargins()
        h_margins = margins.left() + margins.right()
        v_margins = margins.top() + margins.bottom()
        btn_width = self._play_btn.width() + self._add_to_playlist_btn.width()
        desc_width = width - btn_width - h_spacing - h_margins
        desc_height = desc_fm.boundingRect(
            QRect(0, 0, desc_width, 0), Qt.TextFlag.TextWordWrap, self._desc_label.text()
        ).height()
        title_height = 16
        total_height = title_height + desc_height + v_spacing + v_margins
        return total_height

    def _on_play_clicked(self):
        if self._matched_song is not None:
            self._app.playlist.play_model(self._matched_song)
        else:
            aio.run_afn_ref(self.match_and_play)

    def _on_add_to_playlist_clicked(self):
        if self._matched_song is not None:
            self._app.playlist.add(self._matched_song)
        else:
            aio.run_afn_ref(self.match_and_add_to_playlist)

    async def match_and_play(self):
        await self.match()
        if self._matched_song:
            self._app.playlist.play_model(self._matched_song)

    async def match_and_add_to_playlist(self):
        await self.match()
        if self._matched_song:
            self._app.playlist.add(self._matched_song)

    async def match(self):
        async with self._match_lock:
            return await self.match_no_lock()

    async def match_no_lock(self):
        if self._matched_song is not None:
            return self._matched_song

        for btn in self._btns:
            btn.setEnabled(False)
            btn.setToolTip("正在匹配资源...")
        try:
            self._matched_song = await AISongMatcher(self._app).match(self._ai_song)
        except Exception:
            logger.exception("match ai song failed")
            for btn in self._btns:
                btn.setEnabled(True)
        else:
            if self._matched_song is not None:
                for btn in self._btns:
                    btn.setEnabled(True)
            else:
                for btn in self._btns:
                    btn.setToolTip("匹配资源失败")


class AISongListWidget(QWidget):
    """Container widget to display AISongModel list."""

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._title_label = QLabel("歌曲候选列表")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._list_widget = QListWidget(self)
        self._list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list_widget.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        layout.addWidget(self._title_label)
        layout.addWidget(self._list_widget)

        self.setAutoFillBackground(True)

    def set_ai_songs(self, ai_songs: List[AISongModel]):
        self._clear_items()
        for ai_song in ai_songs:
            item = AISongItemWidget(self._app, ai_song, parent=self)
            list_item = QListWidgetItem(self._list_widget)
            width = self._get_width_for_items()
            list_item.setSizeHint(QSize(width, item.height_for_width(width)))
            self._list_widget.addItem(list_item)
            self._list_widget.setItemWidget(list_item, item)

    def _clear_items(self):
        self._list_widget.clear()

    def _get_width_for_items(self):
        margins = self.layout().contentsMargins()
        return self.width() - ScrollBarWidth * 2 - margins.left() - margins.right()

    def resizeEvent(self, event: QResizeEvent):
        """Update item sizes when widget is resized."""
        super().resizeEvent(event)
        self._update_item_sizes()

    def _update_item_sizes(self):
        """Update all item sizes based on current viewport width."""
        width = self._get_width_for_items()
        if width <= 0:
            return

        for i in range(self._list_widget.count()):
            list_item = self._list_widget.item(i)
            item_widget = self._list_widget.itemWidget(list_item)
            if item_widget is not None:
                height = item_widget.height_for_width(width)
                list_item.setSizeHint(QSize(width, height))


class AIChatBox(QWidget):
    """
    A lightweight AI chat UI for the AI Radio page.
    This only provides UI; real message sending is intentionally left empty.
    """

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.copilot = self._app.ai.get_copilot()

        self._header = MidHeader("AI 助手")
        self._new_thread_btn = PlusButton(length=12)
        self._new_thread_btn.setToolTip("新的对话")
        self.history_widget = ChatHistoryWidget(self)
        self.input_widget = ChatInputWidget(self)

        self.input_widget.send_clicked.connect(
            lambda q: aio.run_afn_ref(self.exec_user_query, q)
        )
        self._new_thread_btn.clicked.connect(self.on_new_thread_btn_clicked)
        self.copilot.working_state_changed.connect(self.on_working_state_changed)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header_layout = QHBoxLayout()
        header_layout.addWidget(self._header)
        header_layout.addWidget(self._new_thread_btn)
        header_layout.addStretch(0)
        layout.addLayout(header_layout)
        layout.addWidget(self.history_widget)
        layout.addWidget(self.input_widget)

    async def exec_user_query(self, query: str):
        self.history_widget.add_message("user", query)
        self.history_widget.scroll_to_bottom()

        current_label = None
        response_message = ""
        last_update_ts = time.time()

        async for token, metadata in self.copilot.astream_user_query(query):
            node = metadata["langgraph_node"]
            if node == "model":
                if current_label is None:
                    current_label = self.history_widget.create_message_label(
                        "assistant", ""
                    )
                for block in token.content_blocks:
                    if block["type"] == "text":
                        response_message += block["text"]
                if last_update_ts + 0.2 <= time.time():
                    current_label.setText(response_message)
                    self.history_widget.scroll_to_bottom()
                    last_update_ts = time.time()
            elif node == "tools":
                self.history_widget.create_message_label(
                    "tools", f"tools: {token.name}"
                )
                current_label = None

        if current_label is not None:
            current_label.setText(response_message)
        self.history_widget.scroll_to_bottom()

    def on_new_thread_btn_clicked(self):
        self.copilot.new_thread()
        self.history_widget.clear()

    def on_working_state_changed(self, working: bool):
        self.input_widget.enable_send(not working)


class Body(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app
        copilot = self._app.ai.get_copilot()
        copilot.candidates_changed.connect(
            self.on_copilot_candidates_changed, aioqueue=True)

        self._list_widget = AISongListWidget(app, self)
        self._chat_box = AIChatBox(app)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self._layout.addWidget(self._chat_box)
        self._layout.addWidget(self._list_widget)
        self._layout.setStretch(0, 2)
        self._layout.setStretch(1, 1)
        self.setAutoFillBackground(True)

    def on_copilot_candidates_changed(self, candidates):
        self._list_widget.set_ai_songs(candidates)


def create_aichat_overlay(app: "GuiApp", parent=None) -> AppOverlayContainer:
    """Create an overlay for the AI chat"""
    body = Body(app)
    overlay = AppOverlayContainer(app, body, parent=parent)
    return overlay


if __name__ == "__main__":
    from feeluown.gui.debug import mock_app, simple_layout

    with simple_layout(theme="dark") as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        overlay = create_aichat_overlay(app)
        long_description = (
            "一个很长的描述啊啊啊啊啊啊"
            "啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊"
            "啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊结束"
        )
        sample_ai_songs = [
            AISongModel(
                title="Song A", artists_name="Artist A", description=long_description
            ),
            AISongModel(title="Song B", artists_name="Artist B", description="Desc B"),
            AISongModel(title="Song C", artists_name="Artist C", description="Desc C"),
        ]

        overlay.body._chat_box.history_widget.add_message("user", "hello world")
        overlay.body._chat_box.history_widget.add_message("assistant", "Hi, 我是你的音乐助手")
        overlay.body._chat_box.history_widget.add_message("tools", "tools: play_model")
        overlay.body._list_widget.set_ai_songs(sample_ai_songs)
        overlay.show()
        layout.addWidget(overlay)
