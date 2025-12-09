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

from feeluown.gui.consts import ScrollBarWidth
from feeluown.ai import AISongModel
from feeluown.gui.widgets import PlayButton
from feeluown.gui.widgets.ai_chat import AIChatBox
from feeluown.gui.components.overlay import AppOverlayContainer

from feeluown.app.gui_app import GuiApp


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
        font = self._desc_label.font()
        font.setPixelSize(12)
        self._desc_label.setFont(font)
        palette = self._desc_label.palette()
        palette.setColor(
            QPalette.ColorRole.Text,
            palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text),
        )
        self._desc_label.setPalette(palette)
        self._spacing = 6
        self._margins = 6
        self._setup_ui()

    def _setup_ui(self):
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*([self._margins] * 4))
        layout.setSpacing(self._spacing)

        label_layout = QVBoxLayout()
        label_layout.addWidget(self._title_label)
        label_layout.addWidget(self._desc_label)
        label_layout.addStretch(0)

        layout.addLayout(label_layout)
        layout.addStretch(0)
        layout.addWidget(self._play_btn)

    def height_for_width(self, width) -> QSize:
        desc_fm = QFontMetrics(self._desc_label.font())
        desc_width = width - self._play_btn.width() - self._spacing - self._margins * 2
        desc_height = desc_fm.boundingRect(
            QRect(0, 0, desc_width, 0), Qt.TextFlag.TextWordWrap, self._desc_label.text()
        ).height()
        title_height = 16
        total_height = title_height + desc_height + self._spacing + self._margins * 2
        return total_height

    def _on_play_clicked(self):
        if self._matched_song is not None:
            self._app.playlist.play_model(self._matched_song)


class AISongListWidget(QWidget):
    """Container widget to display AISongModel list."""

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._title_label = QLabel("AI 电台候选歌曲")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._list_widget = QListWidget(self)
        self._list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget.setSpacing(8)
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._title_label)
        layout.addWidget(self._list_widget)

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


class Body(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app
        radio = self._app.ai.get_radio()
        radio.candidates_changed.connect(self.on_radio_candidates_changed, aioqueue=True)

        self._list_widget = AISongListWidget(app, self)
        self._chat_box = AIChatBox(radio._agent, radio._agent_context, "AI 电台")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self._layout.addWidget(self._chat_box)
        self._layout.addWidget(self._list_widget)
        self._layout.setStretch(0, 2)
        self._layout.setStretch(1, 1)
        self.setAutoFillBackground(True)

    def on_radio_candidates_changed(self, candidates):
        self._list_widget.set_ai_songs(candidates)


def create_aichat_overlay(app: "GuiApp", parent=None) -> AppOverlayContainer:
    """Create an overlay for the AI chat"""
    body = Body(app)
    overlay = AppOverlayContainer(app, body, parent=parent)
    return overlay


if __name__ == "__main__":
    from PyQt6.QtCore import QSize
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
        overlay.body._list_widget.set_ai_songs(sample_ai_songs)
        overlay.show()
        layout.addWidget(overlay)
