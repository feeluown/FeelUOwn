import asyncio
import logging
import random
from contextlib import suppress

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from requests.exceptions import RequestException

from fuocore import ModelType
from fuocore import aio
from fuocore.reader import wrap
from fuocore.media import Media, MediaType
from fuocore.excs import ProviderIOError
from fuocore.models import GeneratorProxy, reverse
from fuocore.utils import reader_to_list

from feeluown.helpers import async_run, BgTransparentMixin, disconnect_slots_if_has
from feeluown.widgets.album import AlbumListModel, AlbumListView, AlbumFilterProxyModel
from feeluown.widgets.songs import SongsTableModel, SongsTableView, SongFilterProxyModel
from feeluown.widgets.meta import TableMetaWidget
from feeluown.widgets.table_toolbar import SongsTableToolbar
from feeluown.widgets.tabbar import TableTabBarV2

logger = logging.getLogger(__name__)


def fetch_album_cover_wrapper(img_mgr):
    async def fetch_album_cover(album, cb, uid):
        # try get from cache first
        content = img_mgr.get_from_cache(uid)
        if content is not None:
            return cb(content)
        # FIXME: sleep random second to avoid send too many request to provider
        await asyncio.sleep(random.randrange(100) / 100)
        with suppress(ProviderIOError, RequestException):
            cover = await async_run(lambda: album.cover)
            if cover:  # check if cover url is valid
                # FIXME: we should check if cover is a media object
                if not isinstance(cover, str):
                    cover = cover.url
            url = cover
            if url:
                content = await img_mgr.get(url, uid)
                cb(content)
    return fetch_album_cover


class Renderer:
    async def setUp(self, container):
        # pylint: disable=attribute-defined-outside-init
        self.container = container
        self.meta_widget = container.meta_widget
        self.desc_widget = container.desc_widget
        self.toolbar = container.toolbar
        self.tabbar = container.tabbar
        self.songs_table = container.songs_table
        self.albums_table = container.albums_table
        # pylint: disable=protected-access
        self._app = container._app

        self.real_show_model = container.show_model

    async def render(self):
        """render contents in table container

        please follow the following rendering order:

        1. show meta widget and basic metadata, bind signal if needed
        2. fetch data and show content in table, bind signal if needed
        3. fetch description and show, bind signal if needed
        """

    async def tearDown(self):
        pass

    #
    # utils function for renderer
    #
    async def show_cover(self, cover, cover_uid, as_background=False):
        cover = Media(cover, MediaType.image)
        url = cover.url
        app = self._app
        content = await app.img_mgr.get(url, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            if as_background:
                self.meta_widget.set_cover_pixmap(None)
                self._app.ui.right_panel.show_background_image(pixmap)
            else:
                self._app.ui.right_panel.show_background_image(None)
                self.meta_widget.set_cover_pixmap(pixmap)
            self._app.ui.table_container.updateGeometry()

    def show_model(self, model):
        aio.create_task(self.real_show_model(model))

    def show_albums(self, albums_g):
        # always bind signal first
        # album list filters
        # show the layout
        self.container.current_table = self.albums_table

        # fill the data
        filter_model = AlbumFilterProxyModel(self.albums_table)
        model = AlbumListModel(albums_g,
                               fetch_album_cover_wrapper(self._app.img_mgr),
                               parent=self.albums_table)
        filter_model.setSourceModel(model)
        self.albums_table.setModel(filter_model)
        self.albums_table.scrollToTop()
        disconnect_slots_if_has(self._app.ui.magicbox.filter_text_changed)
        self._app.ui.magicbox.filter_text_changed.connect(filter_model.filter_by_text)

    def show_songs(self, songs=None, songs_g=None, show_count=False):
        self.container.current_table = self.songs_table
        self.toolbar.show()

        if show_count:
            if songs is not None:
                self.meta_widget.songs_count = len(songs)
            if songs_g is not None:
                count = songs_g.count
                self.meta_widget.songs_count = -1 if count is None else count

        songs = songs or []
        logger.debug('Show songs in table, total: %d', len(songs))
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = SongsTableModel(
            source_name_map=source_name_map,
            songs_g=songs_g,
            songs=songs,
            parent=self.songs_table)
        filter_model = SongFilterProxyModel(self.songs_table)
        filter_model.setSourceModel(model)
        self.songs_table.setModel(filter_model)
        self.songs_table.scrollToTop()
        disconnect_slots_if_has(self._app.ui.magicbox.filter_text_changed)
        self._app.ui.magicbox.filter_text_changed.connect(filter_model.filter_by_text)

    def show_desc(self, desc):
        self.container.current_table = None
        self.desc_widget.setText(desc)
        self.desc_widget.show()


class ArtistRenderer(Renderer):
    def __init__(self, artist):
        self.artist = artist

    async def render(self):
        artist = self.artist

        # bind signal first
        # we only show album that implements create_albums_g
        if artist.meta.allow_create_albums_g:
            self.toolbar.filter_albums_needed.connect(
                lambda types: self.albums_table.model().filter_by_types(types))
            self.tabbar.show_albums_needed.connect(
                lambda: self.show_albums(self.artist.create_albums_g()))
            self.albums_table.show_album_needed.connect(self.show_model)
        if hasattr(artist, 'contributed_albums') and artist.contributed_albums:
            # show contributed_album list
            self.tabbar.show_contributed_albums_needed.connect(
                lambda: self.show_albums(self.artist.create_contributed_albums_g()))

        # fetch and render basic metadata
        self.meta_widget.title = artist.name
        self.meta_widget.show()
        self.tabbar.show()
        self.tabbar.artist_mode()

        # fetch and render songs
        songs = songs_g = None
        if artist.meta.allow_create_songs_g:
            songs_g = wrap(artist.create_songs_g())
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(songs_g=wrap(artist.create_songs_g()),
                                        songs=songs,
                                        show_count=True))
        else:
            songs = await async_run(lambda: artist.songs)
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(songs_g=None,
                                        songs=songs,
                                        show_count=True))
        self.show_songs(songs_g=songs_g, songs=songs, show_count=True)

        # finally, we render cover and description
        cover = await async_run(lambda: artist.cover)
        if cover:

            aio.create_task(
                self.show_cover(cover, reverse(artist, '/cover'), as_background=True))

        self.tabbar.show_desc_needed.connect(lambda: aio.create_task(self._show_desc()))

    async def _show_desc(self):
        with suppress(ProviderIOError, RequestException):
            desc = await async_run(lambda: self.artist.desc)
            self.show_desc(desc)


class PlaylistRenderer(Renderer):
    def __init__(self, playlist):
        self.playlist = playlist

    async def render(self):
        playlist = self.playlist

        # show playlist title
        self.meta_widget.show()
        self.meta_widget.title = playlist.name

        # show playlist song list
        songs = songs_g = None
        with suppress(ProviderIOError):
            if playlist.meta.allow_create_songs_g:
                songs_g = GeneratorProxy.wrap(playlist.create_songs_g())
            else:
                songs = await async_run(lambda: playlist.songs)
            self.show_songs(songs=songs, songs_g=songs_g, show_count=True)

        # show playlist cover
        if playlist.cover:
            aio.create_task(
                self.show_cover(playlist.cover, reverse(playlist, '/cover')))

        def remove_song(song):
            playlist.remove(song.identifier)

        self.songs_table.remove_song_func = remove_song
        self.tabbar.show_desc_needed.connect(lambda: aio.create_task(self._show_desc()))

    async def _show_desc(self):
        with suppress(ProviderIOError):
            desc = await async_run(lambda: self.playlist.desc)
            self.show_desc(desc)


class AlbumRenderer(Renderer):
    def __init__(self, album):
        self.album = album

    async def render(self):
        album = self.album

        songs = await async_run(lambda: album.songs)
        self.show_songs(songs)

        self.meta_widget.title = album.name_display
        self.meta_widget.songs_count = len(songs)
        self.meta_widget.creator = album.artists_name_display
        self.meta_widget.show()

        # fetch cover and description
        cover = await async_run(lambda: album.cover)
        if cover:
            aio.create_task(self.show_cover(cover, reverse(album, '/cover')))

        self.tabbar.show()
        self.tabbar.album_mode()
        self.tabbar.show_desc_needed.connect(lambda: aio.create_task(self._show_desc()))
        self.tabbar.show_songs_needed.connect(lambda: self.show_songs(songs))

    async def _show_desc(self):
        with suppress(ProviderIOError):
            desc = await async_run(lambda: self.album.desc)
            self.show_desc(desc)


class SongsCollectionRenderer(Renderer):
    def __init__(self, collection):
        self.collection = collection

    async def render(self):
        collection = self.collection
        self.meta_widget.show()
        self.meta_widget.title = collection.name
        self.meta_widget.updated_at = collection.updated_at
        self.meta_widget.created_at = collection.created_at
        self.show_songs([model for model in collection.models
                         if model.meta.model_type == ModelType.song])
        self.songs_table.remove_song_func = collection.remove


class AlbumsCollectionRenderer(Renderer):
    def __init__(self, reader):
        self.reader = reader

    async def render(self):
        # always bind signals first
        self.toolbar.filter_albums_needed.connect(
            lambda types: self.albums_table.model().filter_by_types(types))
        self.albums_table.show_album_needed.connect(self.show_model)

        self.show_albums(self.reader)


class PlayerPlaylistRenderer(Renderer):

    async def render(self):
        player = self._app.player
        playlist = player.playlist

        songs = playlist.list()
        self.show_songs(songs=songs.copy())
        self.songs_table.remove_song_func = playlist.remove

        # scroll to current song
        current_song = self._app.playlist.current_song
        if current_song is not None:
            row = songs.index(current_song)
            model_index = self.songs_table.model().index(row, 0)
            self.songs_table.scrollTo(model_index)
            self.songs_table.selectRow(row)


class DescLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setContentsMargins(30, 15, 30, 10)
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)


class TableContainer(QFrame, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._renderer = None
        self._table = None  # current visible table
        self._tables = []

        self.toolbar = SongsTableToolbar()
        self.tabbar = TableTabBarV2()
        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)
        self.albums_table = AlbumListView(parent=self)
        self.desc_widget = DescLabel(parent=self)

        self._tables.append(self.songs_table)
        self._tables.append(self.albums_table)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: self._app.browser.goto(model=artist))
        self.songs_table.show_album_needed.connect(
            lambda album: self._app.browser.goto(model=album))

        self.toolbar.play_all_needed.connect(self.play_all)
        self.songs_table.add_to_playlist_needed.connect(self._add_songs_to_playlist)

        self._setup_ui()

    def _setup_ui(self):
        self.current_table = None
        self.tabbar.hide()
        self.meta_widget.add_tabbar(self.tabbar)
        self.desc_widget.hide()

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.toolbar)
        self._layout.addWidget(self.desc_widget)
        self._layout.addWidget(self.songs_table)
        self._layout.addWidget(self.albums_table)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    @property
    def current_table(self):
        """current visible table, if no table is visible, return None"""
        return self._table

    @current_table.setter
    def current_table(self, table):
        """set table as current visible table

        show table and hide other tables, if table is None,
        hide all tables.
        """
        for t in self._tables:
            if t != table:
                t.hide()
        if table is None:
            self.toolbar.hide()
        else:
            self.desc_widget.hide()
            table.show()
            if table is self.albums_table:
                self.toolbar.albums_mode()
            if table is self.songs_table:
                self.toolbar.songs_mode()
        self._table = table

    async def set_renderer(self, renderer):
        """set ui renderer

        TODO: add lock for set_renderer
        """

        if renderer is None:
            return

        # firstly, tear down everything
        # tear down last renderer
        if self._renderer is not None:
            await self._renderer.tearDown()
        self.meta_widget.hide()
        self.meta_widget.clear()
        self.tabbar.hide()
        self.tabbar.check_default()
        self.current_table = None
        # clean right_panel background image
        self._app.ui.right_panel.show_background_image(None)
        # disconnect songs_table signal
        signals = (
            self.tabbar.show_contributed_albums_needed,
            self.tabbar.show_albums_needed,
            self.tabbar.show_songs_needed,
            self.tabbar.show_desc_needed,
            self.albums_table.show_album_needed,
        )
        for signal in signals:
            disconnect_slots_if_has(signal)

        # unbind some callback function
        self.songs_table.remove_song_func = None

        # secondly, prepare environment
        self.show()

        # thirdly, setup new renderer
        await renderer.setUp(self)
        self._renderer = renderer
        await self._renderer.render()

    async def play_song(self, song):
        self._app.player.play_song(song)

    def play_all(self):
        task_name = 'play-all'
        task_spec = self._app.task_mgr.get_or_create(task_name)

        def songs_g_readall_cb(task):
            with suppress(ProviderIOError, asyncio.CancelledError):
                songs = task.result()
                self._app.player.play_songs(songs=songs)
            self.toolbar.enter_state_playall_end()

        model = self.songs_table.model()
        # FIXME: think about a more elegant way
        songs_g = model.sourceModel().songs_g
        if songs_g is not None:
            if songs_g.count is not None:
                task = task_spec.bind_blocking_io(reader_to_list, songs_g)
                self.toolbar.enter_state_playall_start()
                task.add_done_callback(songs_g_readall_cb)
                return
        songs = model.sourceModel().songs
        self._app.player.play_songs(songs=songs)

    async def show_model(self, model):
        model_type = ModelType(model.meta.model_type)
        if model_type == ModelType.album:
            renderer = AlbumRenderer(model)
        elif model_type == ModelType.artist:
            renderer = ArtistRenderer(model)
        elif model_type == ModelType.playlist:
            renderer = PlaylistRenderer(model)
        else:
            renderer = None
        await self.set_renderer(renderer)

    def show_collection(self, coll):
        renderer = SongsCollectionRenderer(coll)
        aio.create_task(self.set_renderer(renderer))

    def show_songs(self, songs=None, songs_g=None):
        """(DEPRECATED) provided only for backward compatibility"""
        renderer = Renderer()
        task = aio.create_task(self.set_renderer(renderer))
        task.add_done_callback(
            lambda _: renderer.show_songs(songs=songs, songs_g=songs_g))

    def show_albums_coll(self, albums_g):
        aio.create_task(self.set_renderer(AlbumsCollectionRenderer(albums_g)))

    def show_player_playlist(self):
        aio.create_task(self.set_renderer(PlayerPlaylistRenderer()))

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def _add_songs_to_playlist(self, songs):
        for song in songs:
            self._app.playlist.add(song)
