import logging
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.library import SupportsRecListDailyPlaylists, SupportsRecACollectionOfSongs
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


class View(QWidget, BgTransparentMixin):

    def __init__(self, app: 'GuiApp'):
        super().__init__(parent=None)
        self._app = app

        self.header_playlist_list = LargeHeader('一些歌单')
        self.header_songs_list = LargeHeader('随便听听')
        self.playlist_list_view = PlaylistCardListView(no_scroll_v=True)
        self.playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(
                self.playlist_list_view,
                card_min_width=150,
            )
        )
        self.songs_list_view = SongMiniCardListView(no_scroll_v=True)
        self.songs_list_view.setItemDelegate(
            SongMiniCardListDelegate(self.songs_list_view, )
        )

        self._layout = QVBoxLayout(self)
        self._setup_ui()

        self.playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model)
        )
        self.songs_list_view.play_song_needed.connect(self._app.playlist.play_model)

    def _setup_ui(self):
        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.header_playlist_list)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.playlist_list_view)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.header_songs_list)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.songs_list_view)
        self._layout.addStretch(0)

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

    async def _get_rec_songs(self):
        providers = self._app.library.list()
        titles = []
        songs = []
        for coro in as_completed([
            run_fn(provider.rec_a_collection) for provider in providers
            if isinstance(provider, SupportsRecACollectionOfSongs)
        ]):
            try:
                title, songs_ = await coro
            except:  # noqa
                logger.exception('get rec songs failed')
            else:
                songs.extend(songs_)
                titles.append(title)
        return titles, songs

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

        titles, songs = await self._get_rec_songs()
        songs_model = SongMiniCardListModel(
            create_reader(songs),
            fetch_image=fetch_cover_wrapper(self._app),
        )
        self.songs_list_view.setModel(songs_model)
        if titles:
            self.header_songs_list.setText(titles[0])
