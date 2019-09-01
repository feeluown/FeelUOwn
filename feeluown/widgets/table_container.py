import asyncio
import logging

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from fuocore import ModelType
from fuocore import aio
from feeluown.helpers import async_run
from feeluown.widgets.songs_table import SongsTableModel, SongsTableView
from feeluown.widgets.table_meta import TableMetaWidget

logger = logging.getLogger(__name__)


class Delegate:
    async def setUp(self, container):
        # pylint: disable=attribute-defined-outside-init
        self.meta_widget = container.meta_widget
        self.toolbar = container.meta_widget.toolbar
        self.songs_table = container.songs_table
        # pylint: disable=protected-access
        self._app = container._app

    async def render(self):
        pass

    async def tearDown(self):
        pass

    #
    # utils function for delegate
    #
    async def show_cover(self, cover):
        app = self._app
        # FIXME: cover_hash may not work properly someday
        cover_uid = cover.split('/', -1)[-1]
        content = await app.img_mgr.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.meta_widget.set_cover_pixmap(pixmap)

    def show_songs(self, songs=None, songs_g=None):
        songs_table = self.songs_table

        songs_table.show()
        songs = songs or []
        logger.debug('Show songs in table, total: %d', len(songs))
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        songs_table.setModel(SongsTableModel(
            source_name_map=source_name_map,
            songs_g=songs_g,
            songs=songs,
            parent=songs_table))
        songs_table.scrollToTop()


class ArtistDelegate(Delegate):
    def __init__(self, artist):
        self.artist = artist

    async def render(self):
        artist = self.artist

        loop = asyncio.get_event_loop()
        songs = songs_g = None
        if artist.meta.allow_create_songs_g:
            songs_g = artist.create_songs_g()
        else:
            songs = await async_run(lambda: artist.songs)
        if songs_g is not None:
            self.show_songs(songs_g=songs_g)
        else:
            self.show_songs(songs=songs)
        desc = await async_run(lambda: artist.desc)
        self.meta_widget.title = artist.name
        self.meta_widget.desc = desc
        self.meta_widget.toolbar.artist_mode()
        cover = await async_run(lambda: artist.cover)
        loop.create_task(self.show_cover(cover))


class PlaylistDelegate(Delegate):
    def __init__(self, playlist):
        self.playlist = playlist

    async def render(self):
        playlist = self.playlist

        loop = asyncio.get_event_loop()
        if playlist.meta.allow_create_songs_g:
            songs_g = playlist.create_songs_g()
            self.show_songs(songs_g=songs_g)
        else:
            songs = await async_run(lambda: playlist.songs, loop=loop)
            self.show_songs(songs)
        self.meta_widget.clear()
        self.meta_widget.title = playlist.name
        desc = await async_run(lambda: playlist.desc)
        self.meta_widget.desc = desc
        if playlist.cover:
            loop.create_task(self.show_cover(playlist.cover))

        def remove_song(song):
            model = self.songs_table.model()
            row = model.songs.index(song)
            msg = 'remove {} from {}'.format(song, playlist)
            with self._app.create_action(msg) as action:
                rv = playlist.remove(song.identifier)
                if rv:
                    model.removeRow(row)
                else:
                    action.failed()
        self.songs_table.song_deleted.connect(lambda song: remove_song(song))


class AlbumDelegate(Delegate):
    def __init__(self, album):
        self.album = album

    async def render(self):
        album = self.album

        loop = asyncio.get_event_loop()
        songs = await async_run(lambda: album.songs)
        self.meta_widget.clear()
        self.show_songs(songs)
        desc = await async_run(lambda: album.desc)
        self.meta_widget.title = album.name
        self.meta_widget.desc = desc
        if album.cover:
            loop.create_task(self.show_cover(album.cover))


class CollectionDelegate(Delegate):
    def __init__(self, collection):
        self.collection = collection

    async def render(self):
        collection = self.collection

        self.meta_widget.clear()
        self.meta_widget.title = collection.name
        self.meta_widget.updated_at = collection.updated_at
        self.meta_widget.created_at = collection.created_at
        self.show_songs(collection.models)
        self.songs_table.song_deleted.connect(collection.remove)


class PlayerPlaylistDelegate(Delegate):

    async def render(self):
        player = self._app.player
        playlist = player.playlist

        self.meta_widget.clear()
        self.show_songs(songs=playlist.list())
        self.songs_table.song_deleted.connect(
            lambda song: self._app.playlist.remove(song))


class TableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: self._app.browser.goto(model=artist))
        self.songs_table.show_album_needed.connect(
            lambda album: self._app.browser.goto(model=album))

        self.meta_widget.toolbar.play_all_needed.connect(self.play_all)
        self.meta_widget.toggle_full_window_needed.connect(self.toggle_meta_full_window)

        self.hide()
        self._setup_ui()

        self._delegate = None

    def _setup_ui(self):
        self.setAutoFillBackground(False)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.songs_table)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    async def set_delegate(self, delegate):
        """set ui delegate

        TODO: add lock for set_delegate
        """

        if delegate is None:
            return

        # firstly, tear down everything
        # tear down last delegate
        if self._delegate is not None:
            await self._delegate.tearDown()
        self.meta_widget.clear()
        # disconnect songs_table signal
        try:
            self.songs_table.song_deleted.disconnect()
        except TypeError:  # no connections at all
            pass

        # secondly, do basic things
        self.show()

        # thirdly, setup new delegate
        await delegate.setUp(self)
        self._delegate = delegate
        await self._delegate.render()

    async def play_song(self, song):
        await async_run(lambda: song.url)
        self._app.player.play_song(song)

    def play_all(self):
        songs = self.songs_table.model().songs
        self._app.player.playlist.clear()
        for song in songs:
            self._app.player.playlist.add(song)
        self._app.player.play_next()

    async def show_model(self, model):
        model_type = ModelType(model.meta.model_type)
        if model_type == ModelType.album:
            delegate = AlbumDelegate(model)
        elif model_type == ModelType.artist:
            delegate = ArtistDelegate(model)
        elif model_type == ModelType.playlist:
            delegate = PlaylistDelegate(model)
        else:
            delegate = None
        await self.set_delegate(delegate)

    def show_collection(self, coll):
        delegate = CollectionDelegate(coll)
        aio.create_task(self.set_delegate(delegate))

    def show_player_playlist(self):
        aio.create_task(self.set_delegate(PlayerPlaylistDelegate()))

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def toggle_meta_full_window(self, fullwindow_needed):
        if fullwindow_needed:
            self.songs_table.hide()
        else:
            self.songs_table.show()
