import asyncio
import logging

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from fuocore import ModelType
from fuocore import aio
from fuocore.media import Media, MediaType
from fuocore.excs import ProviderIOError
from fuocore.models import GeneratorProxy, reverse
from feeluown.helpers import async_run
from feeluown.widgets.album import AlbumListModel, AlbumListView, AlbumFilterProxyModel
from feeluown.widgets.songs_table import SongsTableModel, SongsTableView
from feeluown.widgets.table_meta import TableMetaWidget

logger = logging.getLogger(__name__)


def fetch_image_wrapper(img_mgr):
    def fetch_image(url, cb, uid):
        task = aio.create_task(img_mgr.get(url, uid))
        task.add_done_callback(cb)
    return fetch_image


class Delegate:
    async def setUp(self, container):
        # pylint: disable=attribute-defined-outside-init
        self.meta_widget = container.meta_widget
        self.toolbar = container.meta_widget.toolbar
        self.songs_table = container.songs_table
        self.albums_table = container.albums_table
        # pylint: disable=protected-access
        self._app = container._app

        self.real_show_model = container.show_model

    async def render(self):
        pass

    async def tearDown(self):
        pass

    #
    # utils function for delegate
    #
    async def show_cover(self, cover, cover_uid):
        cover = Media(cover, MediaType.image)
        cover = cover.url
        app = self._app
        content = await app.img_mgr.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.meta_widget.set_cover_pixmap(pixmap)

    def show_model(self, model):
        aio.create_task(self.real_show_model(model))

    def show_albums(self, albums_g):
        self.songs_table.hide()
        self.albums_table.show()
        filter_model = AlbumFilterProxyModel(self.albums_table)
        model = AlbumListModel(albums_g,
                               fetch_image_wrapper(self._app.img_mgr),
                               parent=self.albums_table)
        filter_model.setSourceModel(model)
        self.albums_table.setModel(filter_model)
        self.albums_table.scrollToTop()
        self.meta_widget.toolbar.albums_mode()

    def show_songs(self, songs=None, songs_g=None, show_count=False):
        if show_count:
            if songs is not None:
                self.meta_widget.songs_count = len(songs)
            if songs_g is not None:
                count = songs_g.count
                self.meta_widget.songs_count = -1 if count is None else count

        self.albums_table.hide()
        songs_table = self.songs_table

        songs = songs or []
        logger.debug('Show songs in table, total: %d', len(songs))
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        songs_table.setModel(SongsTableModel(
            source_name_map=source_name_map,
            songs_g=songs_g,
            songs=songs,
            parent=songs_table))
        songs_table.scrollToTop()
        songs_table.show()
        self.meta_widget.toolbar.songs_mode()

    def filter_albums_all(self):
        self.albums_table.model().filter_all()

    def filter_albums_live(self):
        self.albums_table.model().filter_live()

    def filter_albums_mini(self):
        self.albums_table.model().filter_mini()

    def filter_albums_contributed(self):
        self.albums_table.model().filter_contributed()


class ArtistDelegate(Delegate):
    def __init__(self, artist):
        self.artist = artist

    async def render(self):
        artist = self.artist

        self.songs_table.show()

        # bind signal first
        # we only show album that implements create_albums_g
        if artist.meta.allow_create_albums_g:
            # show album detail
            self.albums_table.show_album_needed.connect(self.show_model)

            # show album list
            self.meta_widget.toolbar.show_albums_needed.connect(
                lambda: self.show_albums(self.artist.create_albums_g()))
            # album list fitlers
            self.meta_widget.toolbar.filter_albums_contributed_needed.connect(
                self.filter_albums_contributed)
            self.meta_widget.toolbar.filter_albums_mini_needed.connect(
                self.filter_albums_mini)
            self.meta_widget.toolbar.filter_albums_all_needed.connect(
                self.filter_albums_all)
            self.meta_widget.toolbar.filter_albums_live_needed.connect(
                self.filter_albums_live)

        # fetch and render metadata
        desc = await async_run(lambda: artist.desc)
        self.meta_widget.title = artist.name
        self.meta_widget.desc = desc
        cover = await async_run(lambda: artist.cover)

        # fetch and render songs
        songs = songs_g = None
        if artist.meta.allow_create_songs_g:
            songs_g = artist.create_songs_g()
        else:
            songs = await async_run(lambda: artist.songs)
        self.show_songs(songs_g=songs_g, songs=songs, show_count=True)
        self.meta_widget.toolbar.show_songs_needed.connect(
            lambda: self.show_songs(songs_g=songs_g, songs=songs, show_count=True))

        # render cover
        if cover:
            aio.create_task(self.show_cover(cover, reverse(artist, '/cover')))

        self.meta_widget.toolbar.artist_mode()

    async def tearDown(self):
        pass


class PlaylistDelegate(Delegate):
    def __init__(self, playlist):
        self.playlist = playlist

    async def render(self):
        playlist = self.playlist

        # show playlist title
        self.meta_widget.title = playlist.name

        # show playlist song list
        loop = asyncio.get_event_loop()
        songs = songs_g = None
        try:
            if playlist.meta.allow_create_songs_g:
                songs_g = GeneratorProxy.wrap(playlist.create_songs_g())
            else:
                songs = await async_run(lambda: playlist.songs, loop=loop)
        except ProviderIOError as e:
            self._app.show_msg('read playlist/songs failed：{}'.format(str(e)))
            logger.exception('read playlist/songs failed')
        else:
            self.show_songs(songs=songs, songs_g=songs_g, show_count=True)

        # show playlist description
        try:
            desc = await async_run(lambda: playlist.desc)
        except ProviderIOError as e:
            self._app.show_msg('read playlist/desc failed：{}'.format(str(e)))
        else:
            self.meta_widget.desc = desc

        # show playlist cover
        if playlist.cover:
            loop.create_task(
                self.show_cover(playlist.cover, reverse(playlist, '/cover')))

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
        self.meta_widget.toolbar.pure_songs_mode()


class AlbumDelegate(Delegate):
    def __init__(self, album):
        self.album = album

    async def render(self):
        album = self.album

        loop = asyncio.get_event_loop()
        songs = await async_run(lambda: album.songs)
        self.show_songs(songs)
        desc = await async_run(lambda: album.desc)
        self.meta_widget.title = album.name
        self.meta_widget.desc = desc
        cover = await async_run(lambda: album.cover)
        if cover:
            loop.create_task(self.show_cover(cover, reverse(album, '/cover')))


class CollectionDelegate(Delegate):
    def __init__(self, collection):
        self.collection = collection

    async def render(self):
        collection = self.collection

        self.meta_widget.title = collection.name
        self.meta_widget.updated_at = collection.updated_at
        self.meta_widget.created_at = collection.created_at
        self.show_songs(collection.models)
        self.songs_table.song_deleted.connect(collection.remove)

        self.meta_widget.toolbar.pure_songs_mode()


class PlayerPlaylistDelegate(Delegate):

    async def render(self):
        player = self._app.player
        playlist = player.playlist

        self.show_songs(songs=playlist.list())
        self.songs_table.song_deleted.connect(
            lambda song: self._app.playlist.remove(song))

        self.meta_widget.toolbar.pure_songs_mode()


class TableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)
        self.albums_table = AlbumListView(parent=self)

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
        self._layout.addWidget(self.albums_table)
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
        self.songs_table.hide()
        self.albums_table.hide()
        # disconnect songs_table signal
        signals = (
            self.songs_table.song_deleted,
            self.meta_widget.toolbar.show_albums_needed,
            self.meta_widget.toolbar.show_songs_needed,
            self.albums_table.show_album_needed,
        )
        for signal in signals:
            try:
                signal.disconnect()
            except TypeError:
                pass

        # secondly, prepare environment
        self.show()

        # thirdly, setup new delegate
        await delegate.setUp(self)
        self._delegate = delegate
        await self._delegate.render()

    async def play_song(self, song):
        self._app.player.play_song(song)

    def play_all(self):
        task_name = 'play-all'
        task_spec = self._app.task_mgr.get_or_create(task_name)

        def songs_g_readall_cb(task):
            try:
                songs = task.result()
            except asyncio.CancelledError:
                pass
            except ProviderIOError as e:
                self._app.show_msg('[play-all] read songs failed: {}'.format(str(e)))
            else:
                self._app.player.play_songs(songs=songs)
            finally:
                self.meta_widget.toolbar.enter_state_playall_end()

        model = self.songs_table.model()
        songs_g = model.songs_g
        if songs_g is not None and songs_g.allow_random_read:
            task = task_spec.bind_blocking_io(songs_g.readall)
            self.meta_widget.toolbar.enter_state_playall_start()
            task.add_done_callback(songs_g_readall_cb)
            return
        songs = model.songs
        self._app.player.play_songs(songs=songs)

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

    def show_songs(self, songs=None, songs_g=None):
        """(DEPRECATED) provided only for backward compatibility"""
        delegate = Delegate()
        task = aio.create_task(self.set_delegate(delegate))
        task.add_done_callback(
            lambda _: delegate.show_songs(songs=songs, songs_g=songs_g))

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
