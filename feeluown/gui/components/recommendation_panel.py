from typing import TYPE_CHECKING, Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from feeluown.i18n import t
from feeluown.library import (
    BriefAlbumModel,
    SupportsRecListDailyPlaylists,
    BriefVideoModel,
    BriefSongModel,
)
from feeluown.utils.reader import create_reader
from feeluown.utils.aio import run_fn
from feeluown.gui.widgets.header import LargeHeader
from feeluown.gui.widgets.img_card_list import (
    AlbumCardListView,
    AlbumCardListModel,
    AlbumFilterProxyModel,
    AlbumCardListDelegate,
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
from feeluown.gui.widgets.selfpaint_btn import TriagleButton

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


PlaylistCardMinWidth = 140
PlaylistCardSpacing = 25
SongCardHeight = 50
SongCardPadding = (5, 5, 5, 5)
VideoCardMinWidth = 200


def _resolve_collapsed_row_count(item_count: int, default_row_count: int) -> int:
    # Keep one-row collections compact; otherwise fixed-row layouts leave obvious
    # blank space in discovery panels.
    return 1 if item_count == 1 else default_row_count


class FoldButton(TriagleButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setToolTip(t("fold-tooltip"))
        self.setCheckable(True)
        self.toggled.connect(self.on_toggled)
        # Checked means folded, and show down direction. Click to unfold.
        self.setChecked(True)

    def on_toggled(self, checked):
        self.setToolTip(
            t("fold-expand") if checked else t("fold-collapse"),
        )
        self.set_direction("down" if checked else "up")


class Panel(QWidget):
    # Shared panel chrome for homepage/discovery recommendation blocks.
    _id_pixmap_cache = {}

    def __init__(self, title, body, pixmap, *, show_icon: bool = True):
        super().__init__(parent=None)

        self.icon_label = QLabel()
        self.header = LargeHeader(title)
        self.body = body

        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setPixmap(pixmap)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        self._h_layout = QHBoxLayout()
        self._h_layout.setSpacing(5)
        self._layout.addLayout(self._h_layout)
        # Homepage may aggregate panels from different providers, while
        # provider-scoped pages can hide this icon for a cleaner header.
        if show_icon:
            self._h_layout.addWidget(self.icon_label)
        else:
            self.icon_label.hide()
        self._h_layout.addWidget(self.header)
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
        cls._id_pixmap_cache[provider_id] = pixmap
        return pixmap

    async def render(self):
        pass


class _PlaylistsPanelBase(Panel):
    def __init__(
        self,
        title: str,
        app: "GuiApp",
        provider_id: str,
        *,
        initial_row_count: int = 2,
        show_icon: bool = True,
    ):
        self._app = app
        self._initial_row_count = initial_row_count
        self._collapsed_row_count = initial_row_count
        self.playlist_list_view = PlaylistCardListView(
            no_scroll_v=True, fixed_row_count=self._initial_row_count
        )
        # Bind once at init to avoid duplicate signal connections after re-render.
        self.playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )
        # Keep card visual style consistent between homepage and discovery page.
        self.playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(
                self.playlist_list_view,
                card_min_width=PlaylistCardMinWidth,
                card_spacing=PlaylistCardSpacing,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider_id)
        super().__init__(
            title,
            self.playlist_list_view,
            pixmap,
            show_icon=show_icon,
        )

        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)

    def _show_more_or_less(self, checked):
        # Folded keeps a predictable compact height; unfolded shows all rows.
        if checked:
            self.playlist_list_view.set_fixed_row_count(self._collapsed_row_count)
        else:
            self.playlist_list_view.set_fixed_row_count(-1)

    def set_playlists(self, playlists):
        if not playlists:
            return
        self._collapsed_row_count = _resolve_collapsed_row_count(
            len(playlists), self._initial_row_count
        )
        self.playlist_list_view.set_fixed_row_count(self._collapsed_row_count)
        model = PlaylistCardListModel.create(create_reader(playlists), self._app)
        filter_model = PlaylistFilterProxyModel()
        filter_model.setSourceModel(model)
        self.playlist_list_view.setModel(filter_model)


class RecPlaylistsPanel(_PlaylistsPanelBase):
    def __init__(
        self,
        app: "GuiApp",
        provider: SupportsRecListDailyPlaylists,
        *,
        initial_row_count: int = 2,
        show_icon: bool = True,
    ):
        self._provider = provider
        super().__init__(
            t("recommended-playlist"),
            app,
            provider.identifier,
            initial_row_count=initial_row_count,
            show_icon=show_icon,
        )

    async def render(self):
        playlists = await run_fn(self._provider.rec_list_daily_playlists)
        self.set_playlists(playlists)


class RecPlaylistsCollectionPanel(_PlaylistsPanelBase):
    def __init__(
        self,
        app: "GuiApp",
        provider_id: str,
        title: str,
        playlists,
        *,
        initial_row_count: int = 2,
        show_icon: bool = True,
    ):
        self._playlists = playlists
        super().__init__(
            title,
            app,
            provider_id,
            initial_row_count=initial_row_count,
            show_icon=show_icon,
        )

    async def render(self):
        self.set_playlists(self._playlists)


class RecSongsCollectionPanel(Panel):
    def __init__(
        self,
        app: "GuiApp",
        provider_id: str,
        title: str,
        songs: Sequence[BriefSongModel],
        *,
        initial_row_count: int = 3,
        show_icon: bool = True,
    ):
        self._app = app
        self._songs = songs
        self._initial_row_count = initial_row_count
        self._collapsed_row_count = initial_row_count
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
        songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

        pixmap = Panel.get_provider_pixmap(app, provider_id)
        super().__init__(title, songs_list_view, pixmap, show_icon=show_icon)
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)

    def _show_more_or_less(self, checked):
        if checked:
            self.songs_list_view.set_fixed_row_count(self._collapsed_row_count)
        else:
            self.songs_list_view.set_fixed_row_count(-1)

    async def render(self):
        if not self._songs:
            return
        self._collapsed_row_count = _resolve_collapsed_row_count(
            len(self._songs), self._initial_row_count
        )
        self.songs_list_view.set_fixed_row_count(self._collapsed_row_count)
        model = SongMiniCardListModel.create(create_reader(self._songs), self._app)
        self.songs_list_view.setModel(model)


class RecAlbumsCollectionPanel(Panel):
    def __init__(
        self,
        app: "GuiApp",
        provider_id: str,
        title: str,
        albums: Sequence[BriefAlbumModel],
        *,
        initial_row_count: int = 2,
        show_icon: bool = True,
    ):
        self._app = app
        self._albums = albums
        self._initial_row_count = initial_row_count
        self._collapsed_row_count = initial_row_count
        self.album_list_view = AlbumCardListView(
            no_scroll_v=True, fixed_row_count=self._initial_row_count
        )
        self.album_list_view.show_album_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )
        self.album_list_view.setItemDelegate(
            AlbumCardListDelegate(
                self.album_list_view,
                card_min_width=PlaylistCardMinWidth,
                card_spacing=PlaylistCardSpacing,
            )
        )

        pixmap = Panel.get_provider_pixmap(app, provider_id)
        super().__init__(title, self.album_list_view, pixmap, show_icon=show_icon)
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)

    def _show_more_or_less(self, checked):
        if checked:
            self.album_list_view.set_fixed_row_count(self._collapsed_row_count)
        else:
            self.album_list_view.set_fixed_row_count(-1)

    async def render(self):
        if not self._albums:
            return
        self._collapsed_row_count = _resolve_collapsed_row_count(
            len(self._albums), self._initial_row_count
        )
        self.album_list_view.set_fixed_row_count(self._collapsed_row_count)
        model = AlbumCardListModel.create(create_reader(self._albums), self._app)
        filter_model = AlbumFilterProxyModel()
        filter_model.setSourceModel(model)
        self.album_list_view.setModel(filter_model)


class RecVideosCollectionPanel(Panel):
    def __init__(
        self,
        app: "GuiApp",
        provider_id: str,
        title: str,
        videos: Sequence[BriefVideoModel],
        *,
        initial_row_count: int = 2,
        show_icon: bool = True,
    ):
        self._app = app
        self._videos = videos
        self._initial_row_count = initial_row_count
        self._collapsed_row_count = initial_row_count
        self.video_list_view = VideoCardListView(
            no_scroll_v=True, fixed_row_count=self._initial_row_count
        )
        self.video_list_view.setItemDelegate(
            VideoCardListDelegate(
                self.video_list_view,
                card_min_width=VideoCardMinWidth,
            )
        )
        self.video_list_view.play_video_needed.connect(self._app.playlist.play_model)

        pixmap = Panel.get_provider_pixmap(app, provider_id)
        super().__init__(title, self.video_list_view, pixmap, show_icon=show_icon)
        self.fold_unfold_btn.clicked.connect(self._show_more_or_less)

    def _show_more_or_less(self, checked):
        if checked:
            self.video_list_view.set_fixed_row_count(self._collapsed_row_count)
        else:
            self.video_list_view.set_fixed_row_count(-1)

    async def render(self):
        if not self._videos:
            return
        self._collapsed_row_count = _resolve_collapsed_row_count(
            len(self._videos), self._initial_row_count
        )
        self.video_list_view.set_fixed_row_count(self._collapsed_row_count)
        model = VideoCardListModel.create(self._videos, self._app)
        self.video_list_view.setModel(model)
