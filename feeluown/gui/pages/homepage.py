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
    SupportsCurrentUserChanged,
    SupportsCurrentUser,
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
from feeluown.gui.widgets.selfpaint_btn import PlayButton
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.helpers import BgTransparentMixin

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


async def render(req, **kwargs):
    app: "GuiApp" = req.ctx["app"]

    view = View(app)
    scroll_area = ScrollArea()
    scroll_area.setWidget(view)
    app.ui.right_panel.set_body(scroll_area)
    await view.render()


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
        self._h_layout = QHBoxLayout()
        self._h_layout.setSpacing(5)
        self._layout.addLayout(self._h_layout)
        self._h_layout.addWidget(self.icon_label)
        self._h_layout.addWidget(self.header)
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


class ProviderAccountWidget(QWidget):
    def __init__(self, icon_pixmap, display_name, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setPixmap(icon_pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox.addStretch(1)
        hbox.addWidget(self.icon_label)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        self.name_label = QLabel(display_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 15px; font-weight: 500;")
        layout.addWidget(self.name_label)

        self.setStyleSheet("border-radius: 8px; margin: 2px;")


class Overview(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app
        self._logged_in = {}  # provider_id -> user_name

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(10)

        self._welcome_label = QLabel("Feel Your Own!")
        self._welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; margin: 20px 0; letter-spacing: 2px;")
        self._main_layout.addWidget(self._welcome_label)

        # 分隔线
        self._divider = QLabel()
        self._divider.setFixedHeight(2)
        self._divider.setStyleSheet("margin: 8px 0; background-color: palette(text);")
        self._main_layout.addWidget(self._divider)

        # Title for platform account card area
        self._account_title = QLabel("已连接平台")
        self._account_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._account_title.setStyleSheet(
            "font-size: 15px; font-weight: bold; margin: 8px 0 0 0;")
        self._main_layout.addWidget(self._account_title)

        # Platform account card area
        self._account_layout = QHBoxLayout()
        self._account_layout.setContentsMargins(0, 0, 0, 0)
        self._account_layout.setSpacing(20)
        self._main_layout.addLayout(self._account_layout)

        # Traverse all providers at initialization to detect logged-in platforms
        for provider in self._app.library.list():
            self._try_listen_provider(provider)
            self._update_provider_login_state(provider)

        # Listen for subsequent provider additions
        self._app.library.provider_added.connect(self._on_provider_added)

        self._refresh()

    def _on_provider_added(self, provider):
        self._try_listen_provider(provider)
        self._update_provider_login_state(provider)
        self._refresh()

    def _try_listen_provider(self, provider):
        if isinstance(provider, SupportsCurrentUserChanged):
            provider.current_user_changed.connect(
                lambda user,
                p=provider: self._on_current_user_changed(p, user),
                weak=False
            )

    def _on_current_user_changed(self, provider, user):
        if user is not None:
            self._logged_in[provider.identifier] = user.name
        else:
            self._logged_in.pop(provider.identifier, None)
        self._refresh()

    def _update_provider_login_state(self, provider):
        if isinstance(provider, SupportsCurrentUser):
            try:
                user = provider.get_current_user_or_none()
            except Exception:
                user = None
            if user is not None:
                self._logged_in[provider.identifier] = user.name
            else:
                self._logged_in.pop(provider.identifier, None)

    def _refresh(self):
        # Clean up platform account area
        while self._account_layout.count():
            item = self._account_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Show all providers, display username if logged in,
        # otherwise display platform name
        providers = self._app.library.list()
        if providers:
            for provider in providers:
                pixmap = Panel.get_provider_pixmap(self._app, provider.identifier, 30)
                if provider.identifier in self._logged_in:
                    display_name = self._logged_in[provider.identifier]
                else:
                    display_name = getattr(provider, 'name', provider.identifier)
                widget = ProviderAccountWidget(pixmap, display_name)
                self._account_layout.addWidget(widget)
        else:
            empty_label = QLabel("暂无已连接平台")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("font-size: 15px;")
            self._account_layout.addWidget(empty_label)


class RecPlaylistsPanel(Panel):
    def __init__(self, app: "GuiApp", provider: SupportsRecListDailyPlaylists):
        self._provider = provider
        self._app = app
        title = "推荐歌单"
        self.playlist_list_view = PlaylistCardListView(no_scroll_v=True)
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, self.playlist_list_view, pixmap)

    async def render(self):
        playlists = await run_fn(self._provider.rec_list_daily_playlists)
        print(playlists)
        if not playlists:
            return
        playlist_list_view = self.playlist_list_view
        playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )
        playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(
                playlist_list_view,
                card_min_width=150,
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
        self.songs_list_view = songs_list_view = SongMiniCardListView(no_scroll_v=True)
        songs_list_view.setItemDelegate(
            SongMiniCardListDelegate(
                songs_list_view,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, songs_list_view, pixmap)

        self.play_all_btn = PlayButton()
        self._h_layout.addWidget(self.play_all_btn)
        self._h_layout.addStretch(0)

        self.play_all_btn.clicked.connect(lambda: run_afn(self._play_all))
        songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

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
        self.video_list_view = video_list_view = VideoCardListView()
        video_list_view.setItemDelegate(
            VideoCardListDelegate(
                video_list_view,
                card_min_width=200,
            )
        )
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__("瞅瞅", video_list_view, pixmap)

        video_list_view.play_video_needed.connect(self._app.playlist.play_model)

    async def render(self):
        coll = await run_fn(self._provider.rec_a_collection_of_videos)
        videos = coll.models
        if videos:
            # TODO: maybe show all videos
            model = VideoCardListModel.create(videos[:8], self._app)
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
        self._layout.setSpacing(10)
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
