import logging
from typing import TYPE_CHECKING, Optional, TypeVar, Generic

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from feeluown.library import (
    SupportsRecListDailyPlaylists,
    SupportsRecACollectionOfSongs,
    Collection,
    SupportsRecListDailySongs,
    Provider,
    SupportsRecACollectionOfVideos,
)
from feeluown.utils.reader import create_reader
from feeluown.utils.aio import run_fn, gather, run_afn
from feeluown.gui.widgets.header import LargeHeader
from feeluown.gui.widgets.img_card_list import (
    PlaylistCardListView,
    PlaylistCardListModel,
    PlaylistFilterProxyModel,
    PlaylistCardListDelegate,
    VideoCardListView,
    VideoCardListModel,
    VideoCardListDelegate,
)
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListDelegate,
    SongMiniCardListModel,
)
from feeluown.gui.widgets.selfpaint_btn import PlayButton, TriagleButton
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.helpers import BgTransparentMixin

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


PlaylistCardMinWidth = 140
PlaylistCardSpacing = 25
SongCardHeight = 50
SongCardPadding = (5, 5, 5, 5)  # left, top, right, bottom


async def render(req, **kwargs):
    app: "GuiApp" = req.ctx["app"]

    view = View(app)
    scroll_area = ScrollArea()
    scroll_area.setWidget(view)
    app.ui.right_panel.set_body(scroll_area)
    await view.render()


class FoldButton(TriagleButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setToolTip("展开/收起")
        self.setCheckable(True)
        self.toggled.connect(self.on_toggled)
        # Checked means folded, and show down direction. Click to unfold.
        self.setChecked(True)

    def on_toggled(self, checked):
        self.setToolTip("展开" if checked else "收起")
        self.set_direction("down" if checked else "up")


class Panel(QWidget):
    _id_pixmap_cache = {}

    def __init__(self, title, body, pixmap):
        super().__init__(parent=None)

        self.icon_label = QLabel()
        self.header = LargeHeader(title)
        self.body = body

        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setPixmap(pixmap)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        # Create header layout with icon, title, and buttons
        self._h_layout = QHBoxLayout()
        self._h_layout.setSpacing(5)
        self._layout.addLayout(self._h_layout)

        # Add icon and header to the left
        self._h_layout.addWidget(self.icon_label)
        self._h_layout.addWidget(self.header)

        # Add stretch to push the fold_unfold_btn to the right
        self._h_layout.addStretch(1)

        self.fold_unfold_btn = FoldButton(length=16)
        self._h_layout.addWidget(self.fold_unfold_btn)
        self._h_layout.addSpacing(20)

        self._layout.addWidget(self.body)

    @classmethod
    def get_provider_pixmap(cls, app: "GuiApp", provider_id, width=20):
        device_pixel_ratio = QGuiApplication.instance().devicePixelRatio()
        if provider_id in cls._id_pixmap_cache:
            return cls._id_pixmap_cache[provider_id]
        pvd_ui = app.pvd_ui_mgr.get(provider_id)
        if pvd_ui is None:
            svg = "icons:feeluown.png"
        else:
            svg = pvd_ui.get_colorful_svg()
        pixmap = QPixmap(svg).scaledToWidth(
            int(width * device_pixel_ratio), Qt.TransformationMode.SmoothTransformation
        )
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        return pixmap

    async def render(self):
        pass


class HBody(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)


class Overview(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(10)

        self.setFixedHeight(20)


class RecPlaylistsPanel(Panel):
    def __init__(self, app: "GuiApp", provider: SupportsRecListDailyPlaylists):
        self._provider = provider
        self._app = app
        title = "推荐歌单"
        self._initial_row_count = 2
        self.playlist_list_view = PlaylistCardListView(
            no_scroll_v=True,
            fixed_row_count=self._initial_row_count
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, self.playlist_list_view, pixmap)

        # Connect the fold_unfold_btn to show more or less playlists
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)

    def _show_more_or_less(self, checked):
        if checked:
            self.playlist_list_view.set_fixed_row_count(self._initial_row_count)
        else:
            self.playlist_list_view.set_fixed_row_count(-1)

    async def render(self):
        playlists = await run_fn(self._provider.rec_list_daily_playlists)
        if not playlists:
            return
        playlist_list_view = self.playlist_list_view
        playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )
        playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(
                playlist_list_view,
                card_min_width=PlaylistCardMinWidth,
                card_spacing=PlaylistCardSpacing,
            )
        )
        model = PlaylistCardListModel.create(create_reader(playlists), self._app)
        filter_model = PlaylistFilterProxyModel()
        filter_model.setSourceModel(model)
        playlist_list_view.setModel(filter_model)


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
        super().__init__("每日推荐", app, provider)

    async def render(self):
        songs = await run_fn(self._provider.rec_list_daily_songs)
        self.set_reader(songs)


class RecSongsPanel(SongsBasePanel[SupportsRecACollectionOfSongs]):
    def __init__(self, app: "GuiApp", provider: SupportsRecACollectionOfSongs):
        super().__init__("随便听听", app, provider)

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
            no_scroll_v=True,
            fixed_row_count=self._initial_row_count
        )
        video_list_view.setItemDelegate(
            VideoCardListDelegate(
                video_list_view,
                card_min_width=200,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__("瞅瞅", video_list_view, pixmap)

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
            self.header.setText("暂无推荐视频")
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
        self._layout.addSpacing(20)

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
        gather(*[panel.render() for panel in panels])

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
            return RecPlaylistsPanel(self._app, provider)
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
