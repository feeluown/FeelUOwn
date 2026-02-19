import logging

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame
)

from feeluown.app.gui_app import GuiApp
from feeluown.ai import AISongMatcher
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
        self.ai_radio = self._app.ai.get_copilot()

        # Widgets and layouts
        self._header = Header('AI 电台')
        self._header.setToolTip('暂未实现，欢迎 PR :)')
        self._summary_label = QLabel(self)
        self._summary_label.setWordWrap(True)
        self._cover_label = CoverLabelV2(self._app, self)
        self._status_label = QLabel(self)
        self._play_btn = PlayButton(length=20, padding=0.2)
        self._play_btn.setDisabled(True)
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
        self._status_label.setText('正在获取电台歌曲...')
        ai_songs = await self.ai_radio.recommend_a_song()
        if not ai_songs:
            self._status_label.setText('AI 推荐歌曲失败...')
            logger.warning("AI radio recommend_a_song return empty")
        else:
            first = ai_songs[0]
            self._status_label.setText(f'{first.title} • {first.artists_name}')
            self._summary_label.setText(first.description)
            song = await AISongMatcher(self._app).match(first)
            logger.info(f"matched song: {song}, ai_song: {first}")
            if song is not None:
                self._song = song
                self._play_btn.setEnabled(True)
                self._play_btn.setToolTip('点击播放')
                self._status_label.setText(f'{song.title} • {song.artists_name}')
                cover_media = await aio.run_fn(
                    self._app.library.model_get_cover_media, song
                )
                await self._cover_label.show_cover_media(cover_media, reverse(song))
            else:
                self._play_btn.setToolTip('未匹配到音源')

    def on_play_btn_clicked(self):
        self._app.playlist.play_model(self._song)

    def on_header_clicked(self):
        # TODO: to be implemented
        pass
