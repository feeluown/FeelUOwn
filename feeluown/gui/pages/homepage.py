import logging
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.library import (
    SupportsRecListDailyPlaylists, SupportsRecACollectionOfSongs, Collection,
)
from feeluown.utils.reader import create_reader
from feeluown.utils.aio import run_fn, as_completed
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
    def __init__(self, title, body):
        super().__init__(parent=None)

        self.header = LargeHeader(title)
        self.body = body

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self._layout.addWidget(self.header)
        self._layout.addWidget(self.body)

    async def render(self):
        pass


class RecPlaylistsPanel(Panel):
    def __init__(self, app):
        self._app = app

        title = '一些歌单'
        self.playlist_list_view = playlist_list_view = \
            PlaylistCardListView(no_scroll_v=True)
        playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(
                playlist_list_view,
                card_min_width=150,
            )
        )
        super().__init__(title, playlist_list_view)
        playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )

    async def render(self):
        playlists = await self._get_daily_playlists()
        model = PlaylistCardListModel(
            create_reader(playlists), fetch_cover_wrapper(self._app),
            {p.identifier: p.name
             for p in self._app.library.list()}
        )
        filter_model = PlaylistFilterProxyModel()
        filter_model.setSourceModel(model)
        self.playlist_list_view.setModel(filter_model)

    async def _get_daily_playlists(self):
        providers = self._app.library.list()
        playlists_list = []
        for coro in as_completed([
            run_fn(provider.rec_list_daily_playlists) for provider in providers
            if isinstance(provider, SupportsRecListDailyPlaylists)
        ]):
            try:
                playlists_ = await coro
            except:  # noqa
                logger.exception('get recommended daily playlists failed')
            else:
                playlists_list.append(playlists_)

        playlists = []
        finished = [False] * len(playlists_list)
        while True:
            for i, playlists_ in enumerate(playlists_list):
                try:
                    playlist = playlists_.pop(0)
                except IndexError:
                    finished[i] = True
                else:
                    playlists.append(playlist)
            if all(finished):
                break
        return playlists


class RecSongsPanel(Panel):
    def __init__(self, app):
        self._app = app

        title = '随便听听'
        self.songs_list_view = songs_list_view = SongMiniCardListView(no_scroll_v=True)
        songs_list_view.setItemDelegate(
            SongMiniCardListDelegate(songs_list_view, )
        )
        super().__init__(title, songs_list_view)
        songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

    async def render(self):
        titles, songs = await self._get_rec_songs()
        songs_model = SongMiniCardListModel(
            create_reader(songs),
            fetch_image=fetch_cover_wrapper(self._app),
        )
        self.songs_list_view.setModel(songs_model)
        if titles:
            self.header.setText(titles[0])

    async def _get_rec_songs(self):
        providers = self._app.library.list()
        titles = []
        songs = []
        for coro in as_completed([
            run_fn(provider.rec_a_collection_of_songs) for provider in providers
            if isinstance(provider, SupportsRecACollectionOfSongs)
        ]):
            try:
                coll: Collection = await coro
            except:  # noqa
                logger.exception('get rec songs failed')
            else:
                songs.extend(coll.models)
                titles.append(coll.name)
        return titles, songs


class View(QWidget, BgTransparentMixin):

    def __init__(self, app: 'GuiApp'):
        super().__init__(parent=None)
        self._app = app

        self.rec_playlist_panel = RecPlaylistsPanel(app)
        self.rec_songs_panel = RecSongsPanel(app)

        self._layout = QVBoxLayout(self)
        self._setup_ui()

    def _setup_ui(self):
        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.rec_playlist_panel)
        self._layout.addWidget(self.rec_songs_panel)
        self._layout.addStretch(0)

    async def render(self):
        await self.rec_playlist_panel.render()
        await self.rec_songs_panel.render()
