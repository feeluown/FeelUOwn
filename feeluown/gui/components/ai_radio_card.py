import logging

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame
)

from feeluown.app.gui_app import GuiApp
from feeluown.ai import AIRadioSession, SongSuggestionMatcher
from feeluown.i18n import t
from feeluown.library import reverse
from feeluown.gui.widgets import PlayButton
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.header import LargeHeader
from feeluown.gui.helpers import ClickableMixin, random_solarized_color
from feeluown.utils import aio

logger = logging.getLogger(__name__)


class Header(ClickableMixin, LargeHeader):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, **kwargs)


class AIRadioCard(QFrame):
    def __init__(self, app: GuiApp, parent=None):
        super().__init__(parent)
        self._app = app
        self._radio_preview = AIRadioSession(self._app)

        # Widgets and layouts
        self._header = Header(t("ai-radio-title"))
        self._header.setToolTip(t("ai-radio-activate-tooltip"))
        self._summary_label = QLabel(self)
        self._summary_label.setWordWrap(True)
        self._cover_label = CoverLabelV2(self._app, self)
        self._status_label = QLabel(self)
        self._play_btn = PlayButton(length=20, padding=0.2)
        self._play_btn.setToolTip(t("ai-radio-activate-tooltip"))
        self._play_btn.clicked.connect(self.on_play_btn_clicked)
        self._header.clicked.connect(self.on_header_clicked)
        self.setup_ui()

        self._song = None  # The song which is displayed.

    def setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(8)
        self.setFixedSize(360, 140)
        self._cover_label.setFixedSize(120, 120)
        self.setAutoFillBackground(True)
        self.setStyleSheet('border-radius: 3px; background: palette(window);')
        self._status_label.setStyleSheet('font-size: 15px;')
        self._header.setStyleSheet(
            f"QLabel:hover {{color: '{random_solarized_color().name()}'}};"
        )

        self._label_layout = QVBoxLayout()
        self._label_layout.addWidget(self._header)
        self._label_layout.addWidget(self._summary_label)
        self._label_layout.addStretch(0)
        self._song_layout = QHBoxLayout()
        self._song_layout.addWidget(self._play_btn)
        self._song_layout.addWidget(self._status_label)
        self._label_layout.addLayout(self._song_layout)
        self._layout.addLayout(self._label_layout)
        self._layout.addWidget(self._cover_label)

    async def render(self):
        self._status_label.setText(t("ai-radio-preview-loading"))
        try:
            suggestions = await self._radio_preview.recommend_song_suggestions(1)
        except Exception:  # noqa
            logger.exception("AI radio preview failed")
            suggestions = []
        if not suggestions:
            self._status_label.setText(t("ai-radio-preview-failed"))
            logger.warning("AI radio recommend_song_suggestions return empty")
        else:
            first = suggestions[0]
            self._status_label.setText(f'{first.title} • {first.artists_name}')
            self._summary_label.setText(first.description)
            song = await SongSuggestionMatcher(self._app).match(first)
            logger.info(f"matched song: {song}, suggestion: {first}")
            if song is not None:
                self._song = song
                self._play_btn.setEnabled(True)
                self._play_btn.setToolTip(t("ai-radio-activate-tooltip"))
                self._status_label.setText(f'{song.title} • {song.artists_name}')
                cover_media = await aio.run_fn(
                    self._app.library.model_get_cover_media, song
                )
                await self._cover_label.show_cover_media(cover_media, reverse(song))
            else:
                self._play_btn.setToolTip(t("ai-radio-activate-tooltip"))

    def on_play_btn_clicked(self):
        self.enter_ai_radio()

    def on_header_clicked(self):
        self.enter_ai_radio()

    def enter_ai_radio(self):
        self._app.ai.activate_radio()
        if self._song is not None:
            self._app.fm.candidates.append([self._song])
        self._app.show_msg(t("ai-radio-activated"))
        self._show_ai_chat_overlay()

    def _show_ai_chat_overlay(self):
        overlay = self._app.ui.ai_chat_overlay
        if overlay is not None:
            overlay.show()
            overlay.raise_()
