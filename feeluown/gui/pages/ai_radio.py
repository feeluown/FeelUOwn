import asyncio
from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from feeluown.ai.radio_agent import AIRadio, AISongMatcher, AISongModel
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.widgets import PlayButton
from feeluown.gui.widgets.header import LargeHeader, MidHeader

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render(req, **kwargs):
    app: "GuiApp" = req.ctx["app"]
    view = View(app)
    scroll_area = ScrollArea()
    scroll_area.setWidget(view)
    app.ui.right_panel.set_body(scroll_area)
    await view.render()


class AISongItemWidget(QWidget):
    """Display a single AISongModel with play support."""

    def __init__(self, app: "GuiApp", ai_song: AISongModel, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._ai_song = ai_song
        self._matched_song = None

        self._title_label = QLabel(f"{ai_song.title} • {ai_song.artists_name}")
        self._desc_label = QLabel(ai_song.description)
        self._desc_label.setWordWrap(True)
        self._play_btn = PlayButton(length=18, padding=0.25)
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._on_play_clicked)

        self._setup_ui()

    def _setup_ui(self):
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self._title_label)
        header_layout.addStretch(0)
        header_layout.addWidget(self._play_btn)

        layout.addLayout(header_layout)
        layout.addWidget(self._desc_label)

    def _on_play_clicked(self):
        if self._matched_song is not None:
            self._app.playlist.play_model(self._matched_song)


class AISongListWidget(QWidget):
    """Container widget to display AISongModel list."""

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._status_label = QLabel("AI 电台候选歌曲")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        self._list_widget = QListWidget(self)
        self._list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget.setSpacing(8)
        self._list_widget.setUniformItemSizes(False)
        self._list_widget.setAlternatingRowColors(False)
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._status_label)
        layout.addWidget(self._list_widget)

    def set_ai_songs(self, ai_songs: List[AISongModel]):
        self._clear_items()
        for ai_song in ai_songs:
            item = AISongItemWidget(self._app, ai_song, parent=self)
            list_item = QListWidgetItem(self._list_widget)
            list_item.setSizeHint(item.sizeHint())
            self._list_widget.addItem(list_item)
            self._list_widget.setItemWidget(list_item, item)

    def _clear_items(self):
        self._list_widget.clear()


class View(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app

        self._header = MidHeader("AI 电台候选列表")
        self._list_widget = AISongListWidget(app, self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 10)
        self._layout.setSpacing(12)
        self._layout.addWidget(self._header)
        self._layout.addWidget(self._list_widget)

    async def render(self):
        pass


if __name__ == "__main__":
    """
    Quick manual test for AISongListWidget using debug.mock_app.

    - Mocks AIRadio.get5songs to return sample AISongModel list.
    - Mocks AISongMatcher.match to always succeed.
    """
    import sys

    from feeluown.gui.debug import mock_app, simple_layout

    with simple_layout(theme="dark") as layout, mock_app() as app:
        # minimal attributes used by AISongListWidget / AISongItemWidget
        app.playlist.play_model = lambda _: None
        app.config = type("cfg", (), {})()
        app.ui = type("ui", (), {})()

        widget = AISongListWidget(app)
        layout.addWidget(widget)
        widget.resize(480, 320)
        widget.show()
        # prepare sample data and render
        sample_ai_songs = [
            AISongModel(title="Song A", artists_name="Artist A", description="Desc A"),
            AISongModel(title="Song B", artists_name="Artist B", description="Desc B"),
            AISongModel(title="Song C", artists_name="Artist C", description="Desc C"),
        ]
        widget.set_ai_songs(sample_ai_songs)
