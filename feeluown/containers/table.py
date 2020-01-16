import asyncio
import logging
import random

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from requests.exceptions import RequestException

from fuocore import ModelType
from fuocore import aio
from fuocore.media import Media, MediaType
from fuocore.excs import ProviderIOError
from fuocore.models import GeneratorProxy, reverse
from feeluown.helpers import async_run
from feeluown.widgets.album import AlbumListModel, AlbumListView, AlbumFilterProxyModel
from feeluown.widgets.songs import SongsTableModel, SongsTableView, SongFilterProxyModel
from feeluown.widgets.meta import TableMetaWidget
from feeluown.widgets.table_toolbar import SongsTableToolbar
from feeluown.widgets.tabbar import TableTabBar

logger = logging.getLogger(__name__)


def fetch_album_cover_wrapper(img_mgr):
    async def fetch_album_cover(album, cb, uid):
        # try get from cache first
        content = img_mgr.get_from_cache(uid)
        if content is not None:
            return cb(content)
        # FIXME: sleep random second to avoid send too many request to provider
        await asyncio.sleep(random.randrange(100) / 100)
        try:
            cover = await async_run(lambda: album.cover)
        except (ProviderIOError, RequestException) as e:
            logger.exception('fetch album cover failed: %s', str(e))
        else:
            if cover:  # check if cover url is valid
                # FIXME: we should check if cover is a media object
                if not isinstance(cover, str):
                    cover = cover.url
            url = cover
            if url:
                content = await img_mgr.get(url, uid)
                cb(content)
    return fetch_album_cover


class Delegate:
    async def setUp(self, container):
        # pylint: disable=attribute-defined-outside-init
        self.meta_widget = container.meta_widget
        self.toolbar = container.toolbar
        self.tabbar = container.tabbar
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
    async def show_cover(self, cover, cover_uid, background=False):
        cover = Media(cover, MediaType.image)
        url = cover.url
        app = self._app
        content = await app.img_mgr.get(url, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            if background:
                self.meta_widget.set_cover_pixmap(None)
                self._app.ui.right_panel.show_background_image(pixmap)
            else:
                self._app.ui.right_panel.show_background_image(None)
                self.meta_widget.set_cover_pixmap(pixmap)

    def show_model(self, model):
        aio.create_task(self.real_show_model(model))

    def show_albums(self, albums_g):
        # always bind signal first
        # album list filters
        # show the layout
        self.songs_table.hide()
        self.albums_table.show()
        self.toolbar.albums_mode()

        # fill the data
        filter_model = AlbumFilterProxyModel(self.albums_table)
        model = AlbumListModel(albums_g,
                               fetch_album_cover_wrapper(self._app.img_mgr),
                               parent=self.albums_table)
        filter_model.setSourceModel(model)
        self.albums_table.setModel(filter_model)
        self.albums_table.scrollToTop()
        try:
            self.toolbar.filter_text_changed.disconnect()
        except TypeError:
            pass
        self.toolbar.filter_text_changed.connect(filter_model.filter_by_text)

    def show_songs(self, songs=None, songs_g=None, show_count=False):
        # when is artist mode, we should hide albums_table first
        self.albums_table.hide()
        self.songs_table.show()
        self.toolbar.songs_mode()

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
        try:
            self.toolbar.filter_text_changed.disconnect()
        except TypeError:
            pass
        self.toolbar.filter_text_changed.connect(filter_model.filter_by_text)


class ArtistDelegate(Delegate):
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
            songs_g = artist.create_songs_g()
        else:
            songs = await async_run(lambda: artist.songs)
        self.show_songs(songs_g=songs_g, songs=songs, show_count=True)
        self.tabbar.show_songs_needed.connect(
            lambda: self.show_songs(songs_g=songs_g, songs=songs, show_count=True))

        # finally, we render cover and description
        cover = await async_run(lambda: artist.cover)
        if cover:
            aio.create_task(
                self.show_cover(cover, reverse(artist, '/cover'), background=True))
        self.meta_widget.desc = await async_run(lambda: artist.desc)

    async def tearDown(self):
        pass


class PlaylistDelegate(Delegate):
    def __init__(self, playlist):
        self.playlist = playlist

    async def render(self):
        playlist = self.playlist

        # show playlist title
        self.meta_widget.show()
        self.meta_widget.title = playlist.name

        # show playlist song list
        aio = asyncio.get_event_loop()
        songs = songs_g = None
        try:
            if playlist.meta.allow_create_songs_g:
                songs_g = GeneratorProxy.wrap(playlist.create_songs_g())
            else:
                songs = await async_run(lambda: playlist.songs)
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
            aio.create_task(
                self.show_cover(playlist.cover, reverse(playlist, '/cover')))

        def remove_song(song):
            model = self.songs_table.model()
            # FIXME: think about a more elegant way
            row = model.sourceModel().songs.index(song)
            msg = 'remove {} from {}'.format(song, playlist)
            with self._app.create_action(msg) as action:
                rv = playlist.remove(song.identifier)
                if rv:
                    model.removeRow(row)
                else:
                    action.failed()
        # TODO: remove_song by row may be more elegant
        self.songs_table.song_deleted.connect(lambda song: remove_song(song))


class AlbumDelegate(Delegate):
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
        self.meta_widget.desc = await async_run(lambda: album.desc)


class SongsCollectionDelegate(Delegate):
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
        self.songs_table.song_deleted.connect(collection.remove)


class AlbumsCollectionDelegate(Delegate):
    def __init__(self, reader):
        self.reader = reader

    async def render(self):
        # always bind signals first
        self.toolbar.filter_albums_needed.connect(
            lambda types: self.albums_table.model().filter_by_types(types))
        self.albums_table.show_album_needed.connect(self.show_model)

        self.show_albums(self.reader)


class PlayerPlaylistDelegate(Delegate):

    async def render(self):
        player = self._app.player
        playlist = player.playlist

        songs = playlist.list()
        self.show_songs(songs=songs)
        self.songs_table.song_deleted.connect(
            lambda song: self._app.playlist.remove(song))

        # scroll to current song
        current_song = self._app.playlist.current_song
        if current_song is not None:
            row = songs.index(current_song)
            model_index = self.songs_table.model().index(row, 0)
            self.songs_table.scrollTo(model_index)
            self.songs_table.selectRow(row)


class TableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.toolbar = SongsTableToolbar()
        self.tabbar = TableTabBar()
        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)
        self.albums_table = AlbumListView(parent=self)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: self._app.browser.goto(model=artist))
        self.songs_table.show_album_needed.connect(
            lambda album: self._app.browser.goto(model=album))

        self.toolbar.play_all_needed.connect(self.play_all)
        self.meta_widget.toggle_full_window_needed.connect(self.toggle_meta_full_window)
        self._setup_ui()

        self._delegate = None

    def _setup_ui(self):
        self.toolbar.hide()
        self.meta_widget.add_tabbar(self.tabbar)
        self.setAutoFillBackground(False)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.meta_widget)
        # self._layout.addWidget(self.tabbar)
        self._layout.addWidget(self.toolbar)
        # self._layout.setAlignment(self.tabbar, Qt.AlignRight)
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
        self.meta_widget.hide()
        self.meta_widget.clear()
        self.tabbar.hide()
        self.toolbar.hide()
        self.songs_table.hide()
        self.albums_table.hide()
        # disconnect songs_table signal
        signals = (
            self.songs_table.song_deleted,
            self.tabbar.show_contributed_albums_needed,
            self.tabbar.show_albums_needed,
            self.tabbar.show_songs_needed,
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

        self._app.ui.bottom_panel.update()

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
                self.toolbar.enter_state_playall_end()

        model = self.songs_table.model()
        # FIXME: think about a more elegant way
        songs_g = model.sourceModel().songs_g
        if songs_g is not None and songs_g.allow_random_read:
            task = task_spec.bind_blocking_io(songs_g.readall)
            self.toolbar.enter_state_playall_start()
            task.add_done_callback(songs_g_readall_cb)
            return
        songs = model.sourceModel().songs
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
        delegate = SongsCollectionDelegate(coll)
        aio.create_task(self.set_delegate(delegate))

    def show_songs(self, songs=None, songs_g=None):
        """(DEPRECATED) provided only for backward compatibility"""
        delegate = Delegate()
        task = aio.create_task(self.set_delegate(delegate))
        task.add_done_callback(
            lambda _: delegate.show_songs(songs=songs, songs_g=songs_g))

    def show_albums_coll(self, albums_g):
        aio.create_task(self.set_delegate(AlbumsCollectionDelegate(albums_g)))

    def show_player_playlist(self):
        aio.create_task(self.set_delegate(PlayerPlaylistDelegate()))

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def toggle_meta_full_window(self, fullwindow_needed):
        if fullwindow_needed:
            self.songs_table.hide()
            self.meta_widget.setMaximumHeight(4000)
        else:
            self.meta_widget.setMinimumHeight(self.height()*5//9)
            self.songs_table.show()
        self._app.ui.bottom_panel.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.meta_widget.setMinimumHeight(self.height()*5//9)
