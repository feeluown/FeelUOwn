import logging
from typing import TYPE_CHECKING, Optional, TypeVar, Generic

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from feeluown.i18n import t
from feeluown.library import (
    SupportsRecListDailyPlaylists,
    SupportsRecACollectionOfSongs,
    Collection,
    SupportsRecListDailySongs,
    Provider,
    SupportsRecACollectionOfVideos,
)
from feeluown.utils.aio import run_fn, gather, run_afn
from feeluown.gui.widgets.img_card_list import (
    VideoCardListView,
    VideoCardListModel,
    VideoCardListDelegate,
)
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListDelegate,
    SongMiniCardListModel,
)
from feeluown.gui.widgets.selfpaint_btn import PlayButton
from feeluown.gui.helpers import BgTransparentMixin
from feeluown.gui.pages.recommendation_panels import Panel, RecPlaylistsPanel
from feeluown.gui.pages.template import render_scroll_area_view

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


SongCardHeight = 50
SongCardPadding = (5, 5, 5, 5)  # left, top, right, bottom


async def render(req, **kwargs):
    await render_scroll_area_view(req, View)


class HBody(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)


class Overview(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app

        if self._app.ai is not None:
            from feeluown.gui.components.ai_radio_card import AIRadioCard

            self._ai_radio_card = AIRadioCard(self._app)
        else:
            self._ai_radio_card = None

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(10)
        if self._ai_radio_card is not None:
            self._main_layout.addWidget(self._ai_radio_card)

    async def render(self):
        if self._ai_radio_card is not None:
            await self._ai_radio_card.render()


P = TypeVar("P", bound=Provider)


class SongsBasePanel(Panel, Generic[P]):
    """
    Base panel class for show a list of songs.
    """

    def __init__(self, title: str, app: "GuiApp", provider: P):
        self._app = app
        self._provider = provider
        self._initial_row_count = 3
        self.songs_list_view = songs_list_view = SongMiniCardListView(
            no_scroll_v=True,
            fixed_row_count=self._initial_row_count,
        )
        songs_list_view.setItemDelegate(
            SongMiniCardListDelegate(
                songs_list_view,
                card_height=SongCardHeight,
                card_padding=SongCardPadding,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, songs_list_view, pixmap)

        # Add play_all_btn to the left of the header
        self.play_all_btn = PlayButton()
        # Insert the play button after the header
        self._h_layout.insertWidget(2, self.play_all_btn)

        # Connect buttons
        self.play_all_btn.clicked.connect(lambda: run_afn(self._play_all))
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)
        songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

    def _show_more_or_less(self, checked):
        if checked:
            self.songs_list_view.set_fixed_row_count(self._initial_row_count)
        else:
            self.songs_list_view.set_fixed_row_count(-1)

    async def _play_all(self):
        songs = await run_fn(self.songs_list_view.model().get_reader().readall)
        self._app.playlist.set_models(songs, next_=True)
        self._app.player.resume()

    def set_reader(self, reader):
        songs_model = SongMiniCardListModel.create(reader, self._app)
        self.songs_list_view.setModel(songs_model)


class RecDailySongsPanel(SongsBasePanel[SupportsRecListDailySongs]):
    def __init__(self, app: "GuiApp", provider: SupportsRecListDailySongs):
        super().__init__(t("recommended-daily-playlist"), app, provider)

    async def render(self):
        songs = await run_fn(self._provider.rec_list_daily_songs)
        self.set_reader(songs)


class RecSongsPanel(SongsBasePanel[SupportsRecACollectionOfSongs]):
    def __init__(self, app: "GuiApp", provider: SupportsRecACollectionOfSongs):
        super().__init__(t("recommended-feelin-lucky"), app, provider)

    async def render(self):
        coll: Collection = await run_fn(self._provider.rec_a_collection_of_songs)
        self.set_reader(coll.models)
        self.header.setText(coll.name)


class RecVideosPanel(Panel):
    def __init__(self, app: "GuiApp", provider: SupportsRecACollectionOfVideos):
        self._app = app
        self._provider = provider
        self._initial_row_count = 2
        self.video_list_view = video_list_view = VideoCardListView(
            no_scroll_v=True, fixed_row_count=self._initial_row_count
        )
        video_list_view.setItemDelegate(
            VideoCardListDelegate(
                video_list_view,
                card_min_width=200,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(t("recommended-videos"), video_list_view, pixmap)

        # Connect the fold_unfold_btn to show more or less videos
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)
        video_list_view.play_video_needed.connect(self._app.playlist.play_model)

    def _show_more_or_less(self, checked):
        if checked:
            self.video_list_view.set_fixed_row_count(self._initial_row_count)
        else:
            self.video_list_view.set_fixed_row_count(-1)

    async def render(self):
        coll = await run_fn(self._provider.rec_a_collection_of_videos)
        videos = coll.models
        if videos:
            model = VideoCardListModel.create(videos, self._app)
            self.video_list_view.setModel(model)
            self.header.setText(coll.name)
        else:
            self.header.setText(t("recommended-videos-missing"))
            self.video_list_view.hide()


class View(QWidget, BgTransparentMixin):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app

        self._overview = Overview(app)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(20)
        self._layout.addWidget(self._overview)

    async def render(self):
        panels = []
        settings = self._app.config.NEW_HOMEPAGE_SETTINGS
        for content in settings.get("contents", []):
            name = content["name"]
            if name == "RecListDailySongs":
                panel = self._handle_rec_list_daily_songs(content)
                if panel is not None:
                    panels.append(panel)
            elif name == "RecListDailyPlaylists":
                panel = self._handle_rec_list_daily_playlists(content)
                if panel is not None:
                    panels.append(panel)
            elif name == "RecACollectionOfSongs":
                panel = self._handle_rec_a_collection_of_songs(content)
                if panel is not None:
                    panels.append(panel)
            elif name == "RecACollectionOfVideos":
                panel = self._handle_rec_a_collection_of_videos(content)
                if panel is not None:
                    panels.append(panel)
        for panel in panels:
            self._layout.addWidget(panel)
        gather(*([panel.render() for panel in panels] + [self._overview.render()]))

    def _handle_rec_a_collection_of_videos(self, content: dict) -> Optional[Panel]:
        source = content["provider"]
        provider = self._app.library.get(source)
        if isinstance(provider, SupportsRecACollectionOfVideos):
            return RecVideosPanel(self._app, provider)
        logger.warning(
            f"Invalid homepage content: {content}, "
            f"provider {source} not found or not supported"
        )
        return None

    def _handle_rec_list_daily_songs(self, content: dict) -> Optional[Panel]:
        source = content["provider"]
        provider = self._app.library.get(source)
        if isinstance(provider, SupportsRecListDailySongs):
            return RecDailySongsPanel(self._app, provider)
        logger.warning(
            f"Invalid homepage content: {content}, "
            f"provider {source} not found or not supported"
        )
        return None

    def _handle_rec_list_daily_playlists(self, content: dict) -> Optional[Panel]:
        source = content["provider"]
        provider = self._app.library.get(source)
        if isinstance(provider, SupportsRecListDailyPlaylists):
            # Homepage can mix panels from multiple providers, keep provider icon
            # visible to disambiguate each section's source.
            return RecPlaylistsPanel(self._app, provider, show_icon=True)
        logger.warning(
            f"Invalid homepage content: {content}, "
            f"provider {source} not found or not supported"
        )
        return None

    def _handle_rec_a_collection_of_songs(self, content: dict) -> Optional[Panel]:
        source = content["provider"]
        provider = self._app.library.get(source)
        if isinstance(provider, SupportsRecACollectionOfSongs):
            return RecSongsPanel(self._app, provider)
        logger.warning(
            f"Invalid homepage content: {content}, "
            f"provider {source} not found or not supported"
        )
        return None
