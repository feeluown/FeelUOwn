import logging
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from feeluown.library import (
    SupportsRecListDailyPlaylists, SupportsRecACollectionOfSongs, Collection,
)
from feeluown.utils.reader import create_reader
from feeluown.utils.aio import run_fn, gather
from feeluown.gui.widgets.header import LargeHeader
from feeluown.gui.widgets.img_card_list import (
    PlaylistCardListView,
    PlaylistCardListModel,
    PlaylistFilterProxyModel,
    PlaylistCardListDelegate,
)
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListDelegate,
    SongMiniCardListModel,
)
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.helpers import fetch_cover_wrapper, BgTransparentMixin

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


async def render(req, **kwargs):
    app: 'GuiApp' = req.ctx['app']

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
    def get_provider_pixmap(cls, app: 'GuiApp', provider_id):
        if provider_id in cls._id_pixmap_cache:
            return cls._id_pixmap_cache[provider_id]
        pvd_ui = app.pvd_ui_mgr.get(provider_id)
        svg = pvd_ui.get_colorful_svg()
        return QPixmap(svg).scaledToWidth(20, Qt.SmoothTransformation)

    async def render(self):
        pass


class HBody(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)


class RecPlaylistsPanel(Panel):

    def __init__(self, app: 'GuiApp', provider: SupportsRecListDailyPlaylists):
        self._provider = provider
        self._app = app
        title = '推荐歌单'
        self.playlist_list_view = PlaylistCardListView(no_scroll_v=True)
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, self.playlist_list_view, pixmap)

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
                card_min_width=150,
            )
        )
        model = PlaylistCardListModel(
            create_reader(playlists), fetch_cover_wrapper(self._app),
            {p.identifier: p.name
             for p in self._app.library.list()}
        )
        filter_model = PlaylistFilterProxyModel()
        filter_model.setSourceModel(model)
        playlist_list_view.setModel(filter_model)


class RecSongsPanel(Panel):

    def __init__(self, app: 'GuiApp', provider: SupportsRecACollectionOfSongs):
        self._app = app
        self._provider = provider

        title = '随便听听'
        self.songs_list_view = songs_list_view = SongMiniCardListView(no_scroll_v=True)
        songs_list_view.setItemDelegate(SongMiniCardListDelegate(songs_list_view, ))
        pixmap = Panel.get_provider_pixmap(app, provider.identifier)
        super().__init__(title, songs_list_view, pixmap)
        songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

    async def render(self):
        coll: Collection = await run_fn(self._provider.rec_a_collection_of_songs)
        songs_model = SongMiniCardListModel(
            create_reader(coll.models),
            fetch_image=fetch_cover_wrapper(self._app),
        )
        self.songs_list_view.setModel(songs_model)
        self.header.setText(coll.name)


class View(QWidget, BgTransparentMixin):

    def __init__(self, app: 'GuiApp'):
        super().__init__(parent=None)
        self._app = app

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(0)

    async def render(self):
        panels = []
        providers = self._app.library.list()
        for provider in providers:
            if isinstance(provider, SupportsRecListDailyPlaylists):
                panel = RecPlaylistsPanel(self._app, provider)
                panels.append(panel)
            if isinstance(provider, SupportsRecACollectionOfSongs):
                panel = RecSongsPanel(self._app, provider)
                panels.append(panel)
        for panel in panels:
            self._layout.addWidget(panel)
        gather(*[panel.render() for panel in panels])
