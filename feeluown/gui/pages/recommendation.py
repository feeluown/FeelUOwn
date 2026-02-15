import logging
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QSizePolicy
from feeluown.library.provider_protocol import SupportsToplist

from feeluown.library import (
    SupportsRecListDailyPlaylists,
    SupportsRecListDailySongs,
    SupportsCurrentUserDislikeSongsReader,
    SupportsCurrentUserListRadioSongs,
)

from feeluown.gui.widgets import CalendarButton, RankButton, EmojiButton
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.helpers import BgTransparentMixin
from feeluown.gui.pages.recommendation_panels import RecPlaylistsPanel
from feeluown.i18n import t


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


logger = logging.getLogger(__name__)

# Keep action controls visually comparable with the recommendation panel title/content.
ActionButtonHeight = 34
ActionButtonMinWidth = 170
ActionButtonSpacing = 10


async def render(req, **kwargs):
    app: "GuiApp" = req.ctx["app"]

    view = View(app)
    # Reuse page ScrollArea so this page behaves like homepage when content grows.
    scroll_area = ScrollArea()
    scroll_area.setWidget(view)
    app.ui.right_panel.set_body(scroll_area)
    await view.render()


class View(QWidget, BgTransparentMixin):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app
        self._heart_radar_provider: Optional[SupportsCurrentUserListRadioSongs] = None
        self._playlist_panel: Optional[RecPlaylistsPanel] = None

        self.daily_songs_btn = CalendarButton(
            t("recommended-daily-playlist"),
            height=ActionButtonHeight,
            parent=self,
        )
        self.rank_btn = RankButton(height=ActionButtonHeight, parent=self)
        # FIXME: design a new button for dislike
        self.dislike_btn = EmojiButton(
            "🚫", t("music-blacklisted"), height=ActionButtonHeight, parent=self
        )
        self.heart_radar_btn = EmojiButton(
            "📻", t("music-radio-radar"), height=ActionButtonHeight, parent=self
        )
        # Buttons should have comparable visual weight with the panel title/body.
        self.daily_songs_btn.setMinimumWidth(ActionButtonMinWidth)
        self.rank_btn.setMinimumWidth(ActionButtonMinWidth)
        self.dislike_btn.setMinimumWidth(ActionButtonMinWidth)
        self.heart_radar_btn.setMinimumWidth(ActionButtonMinWidth)
        self._action_btns = [
            self.daily_songs_btn,
            self.rank_btn,
            self.heart_radar_btn,
            self.dislike_btn,
        ]
        # Preserve semantic order when wrapping to 2/1 columns.
        for btn in self._action_btns:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._action_cols = 0
        self._resize_event_source = None

        self._playlist_section = QWidget(self)
        self._playlist_section_layout = QVBoxLayout(self._playlist_section)
        self._playlist_section_layout.setContentsMargins(0, 0, 0, 0)
        self._playlist_section_layout.setSpacing(0)
        self._playlist_section.hide()

        self._layout = QVBoxLayout(self)
        self._setup_ui()

        self.daily_songs_btn.clicked.connect(
            lambda: self._app.browser.goto(page="/rec/daily_songs")
        )
        self.rank_btn.clicked.connect(lambda: self._app.browser.goto(page="/toplist"))
        self.heart_radar_btn.clicked.connect(self._on_heart_radar_clicked)
        self.dislike_btn.clicked.connect(
            lambda: self._app.browser.goto(page="/my_dislike")
        )

    def _setup_ui(self):
        self._action_layout = QGridLayout()
        self._action_layout.setContentsMargins(0, 0, 0, 0)
        self._action_layout.setHorizontalSpacing(ActionButtonSpacing)
        self._action_layout.setVerticalSpacing(ActionButtonSpacing)

        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(0)
        # Keep discovery action buttons as the topmost section to reduce noise.
        self._layout.addLayout(self._action_layout)
        self._layout.addSpacing(20)
        self._layout.addWidget(self._playlist_section)
        self._layout.addStretch(0)
        self._reflow_action_buttons()

    def _calc_action_button_columns(self) -> int:
        self._ensure_resize_event_source()
        margins = self._layout.contentsMargins()
        if self._resize_event_source is not None:
            available_width = self._resize_event_source.width()
        else:
            available_width = self.width()
        available = max(1, available_width - margins.left() - margins.right())
        # cols ~= available width / button footprint, then clamp to [1, button_count].
        unit = ActionButtonMinWidth + ActionButtonSpacing
        cols = (available + ActionButtonSpacing) // unit
        return max(1, min(len(self._action_btns), cols))

    def _reflow_action_buttons(self):
        cols = self._calc_action_button_columns()
        # Avoid unnecessary teardown/rebuild when only height changed.
        if cols == self._action_cols:
            return
        self._action_cols = cols

        while self._action_layout.count():
            item = self._action_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._action_layout.removeWidget(widget)

        for i, btn in enumerate(self._action_btns):
            row, col = divmod(i, cols)
            self._action_layout.addWidget(btn, row, col)

        for col in range(len(self._action_btns)):
            self._action_layout.setColumnStretch(col, 1 if col < cols else 0)

    def _ensure_resize_event_source(self):
        # When hosted by QScrollArea, the viewport width can change while this
        # view width is temporarily constrained by minimum-size hints.
        parent = self.parentWidget()
        if parent is self._resize_event_source:
            return
        if self._resize_event_source is not None:
            self._resize_event_source.removeEventFilter(self)
        self._resize_event_source = parent
        if self._resize_event_source is not None:
            self._resize_event_source.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self._resize_event_source and event.type() == QEvent.Type.Resize:
            self._reflow_action_buttons()
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_resize_event_source()
        self._reflow_action_buttons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_action_buttons()

    async def render(self):
        pvd_ui = self._app.current_pvd_ui_mgr.get()
        if pvd_ui is None:
            self._app.show_msg("wtf!")
            return

        provider = pvd_ui.provider
        if isinstance(provider, SupportsRecListDailyPlaylists):
            if self._playlist_panel is None:
                self._playlist_panel = RecPlaylistsPanel(
                    self._app,
                    provider,
                    title=t("music-customized-recommendation"),
                    initial_row_count=1,
                    # /rec is scoped to the current provider, so provider icon is
                    # redundant here.
                    show_icon=False,
                )
                self._playlist_section_layout.addWidget(self._playlist_panel)
            self._playlist_section.show()
            await self._playlist_panel.render()
        else:
            # Keep action buttons usable even when provider has no daily playlists.
            self._playlist_section.hide()

        self.daily_songs_btn.setEnabled(isinstance(provider, SupportsRecListDailySongs))
        self.rank_btn.setEnabled(isinstance(provider, SupportsToplist))
        self.heart_radar_btn.setEnabled(
            isinstance(provider, SupportsCurrentUserListRadioSongs)
        )
        self.dislike_btn.setEnabled(
            isinstance(provider, SupportsCurrentUserDislikeSongsReader)
        )

    def _on_heart_radar_clicked(self):
        pvd_ui = self._app.current_pvd_ui_mgr.get()
        assert pvd_ui is not None
        provider = pvd_ui.provider
        assert isinstance(provider, SupportsCurrentUserListRadioSongs)

        was_active = self._app.fm.is_active
        current_provider = self._heart_radar_provider if was_active else None
        fetch_func = provider.current_user_list_radio_songs
        if was_active and current_provider is provider:
            self._app.show_msg(t("music-radio-radar-activated"))
            return

        if was_active:
            self._app.fm.deactivate()

        self._app.fm.activate(fetch_func)
        self._heart_radar_provider = provider
        self._app.show_msg(
            t("music-radio-radar-changed")
            if was_active
            else t("music-radio-radar-activated")
        )
