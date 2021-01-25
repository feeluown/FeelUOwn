import asyncio
import logging
import random
import warnings
from contextlib import suppress

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from requests.exceptions import RequestException

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.media import Media, MediaType
from feeluown.excs import ProviderIOError
from feeluown.library import ProviderFlags, ModelState, NotSupported, ModelFlags
from feeluown.models import reverse, ModelType

from feeluown.gui.helpers import async_run, BgTransparentMixin, disconnect_slots_if_has
from feeluown.widgets import TextButton
from feeluown.widgets.album import AlbumListModel, AlbumListView, AlbumFilterProxyModel
from feeluown.widgets.artist import ArtistListModel, ArtistListView, \
    ArtistFilterProxyModel
from feeluown.widgets.video import VideoListModel, VideoListView, \
    VideoFilterProxyModel
from feeluown.widgets.playlist import PlaylistListModel, PlaylistListView, \
    PlaylistFilterProxyModel
from feeluown.widgets.songs import SongsTableModel, SongsTableView, SongFilterProxyModel
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.widgets.meta import TableMetaWidget
from feeluown.widgets.table_toolbar import SongsTableToolbar
from feeluown.widgets.tabbar import TableTabBarV2

logger = logging.getLogger(__name__)


def fetch_cover_wrapper(img_mgr):
    async def fetch_model_cover(model, cb, uid):
        # try get from cache first
        content = img_mgr.get_from_cache(uid)
        if content is not None:
            return cb(content)
        # FIXME: sleep random second to avoid send too many request to provider
        await asyncio.sleep(random.randrange(100) / 100)
        with suppress(ProviderIOError, RequestException):
            cover = await async_run(lambda: model.cover)
            if cover:  # check if cover url is valid
                # FIXME: we should check if cover is a media object
                if not isinstance(cover, str):
                    cover = cover.url
            url = cover
            if url:
                content = await img_mgr.get(url, uid)
                cb(content)
    return fetch_model_cover


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
        self.artists_table = container.artists_table
        self.videos_table = container.videos_table
        self.playlists_table = container.playlists_table
        self.comments_table = container.comments_table
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
    def set_extra(self, extra):
        self.container.current_extra = extra

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
        self._show_model_with_cover(albums_g,
                                    self.albums_table,
                                    AlbumListModel,
                                    AlbumFilterProxyModel)

    def show_artists(self, reader):
        self._show_model_with_cover(reader,
                                    self.artists_table,
                                    ArtistListModel,
                                    ArtistFilterProxyModel)

    def show_videos(self, reader):
        self._show_model_with_cover(reader,
                                    self.videos_table,
                                    VideoListModel,
                                    VideoFilterProxyModel)

    def show_playlists(self, reader):
        self._show_model_with_cover(reader,
                                    self.playlists_table,
                                    PlaylistListModel,
                                    PlaylistFilterProxyModel)

    def _show_model_with_cover(self, reader, table, model_cls, filter_model_cls):
        self.container.current_table = table
        filter_model = filter_model_cls(self.albums_table)
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = model_cls(reader,
                          fetch_cover_wrapper(self._app.img_mgr),
                          parent=self.artists_table,
                          source_name_map=source_name_map)
        filter_model.setSourceModel(model)
        table.setModel(filter_model)
        table.scrollToTop()
        disconnect_slots_if_has(self._app.ui.magicbox.filter_text_changed)
        self._app.ui.magicbox.filter_text_changed.connect(filter_model.filter_by_text)

    def show_songs(self, reader, show_count=False):
        reader = wrap(reader)
        self.container.current_table = self.songs_table
        self.toolbar.show()

        if show_count:
            count = reader.count
            self.meta_widget.songs_count = -1 if count is None else count

        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = SongsTableModel(
            source_name_map=source_name_map,
            reader=reader,
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

    def show_comments(self, comments):
        self.container.current_table = self.comments_table
        reader = wrap(comments)
        model = CommentListModel(reader)
        self.comments_table.setModel(model)


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
        reader = None
        if artist.meta.allow_create_songs_g:
            reader = wrap(artist.create_songs_g())
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(reader=wrap(artist.create_songs_g()),
                                        show_count=True))
        else:
            songs = await async_run(lambda: artist.songs)
            reader = wrap(songs)
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(reader=wrap(songs), show_count=True))
        self.show_songs(reader=reader, show_count=True)

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
        with suppress(ProviderIOError):
            if playlist.meta.allow_create_songs_g:
                reader = wrap(playlist.create_songs_g())
            else:
                songs = await async_run(lambda: playlist.songs)
                reader = wrap(songs)
            self.show_songs(reader=reader, show_count=True)

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
        self.show_songs(wrap(songs))

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
        self.songs_table.remove_song_func = collection.remove
        self._show_songs()

        # only show tabbar if description is not empty
        if self.collection.description:
            self.tabbar.show()
            # FIXME: maybe add a playlist/collection mode for tabbar
            self.tabbar.album_mode()
            self.tabbar.show_songs_needed.connect(self._show_songs)
            self.tabbar.show_desc_needed.connect(
                lambda: self.show_desc(self.collection.description))

    def _show_songs(self):
        """filter model with other type"""
        self.show_songs(wrap([model for model in self.collection.models
                              if model.meta.model_type == ModelType.song]))


class AlbumsCollectionRenderer(Renderer):
    def __init__(self, reader):
        self.reader = reader

    async def render(self):
        # always bind signals first
        self.toolbar.filter_albums_needed.connect(
            lambda types: self.albums_table.model().filter_by_types(types))

        self.show_albums(self.reader)


class ArtistsCollectionRenderer(Renderer):
    def __init__(self, reader):
        self.reader = reader

    async def render(self):
        self.show_artists(self.reader)


class VideosRenderer(Renderer):
    def __init__(self, reader):
        self.reader = reader

    async def render(self):
        self.show_videos(self.reader)


class PlayerPlaylistRenderer(Renderer):

    async def render(self):
        self.meta_widget.title = '当前播放列表'
        self.meta_widget.show()
        player = self._app.player
        playlist = player.playlist

        async def clear_playlist():
            playlist.clear()
            await self.render()  # re-render

        songs = playlist.list()
        self.show_songs(wrap(songs.copy()))
        btn = TextButton('清空', self.toolbar)
        btn.clicked.connect(lambda *args: aio.create_task(clear_playlist()))
        self.toolbar.add_tmp_button(btn)

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
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)


class TableContainer(QFrame, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._renderer = None
        self._table = None  # current visible table
        self._tables = []

        self._extra = None
        self.toolbar = SongsTableToolbar()
        self.tabbar = TableTabBarV2()
        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)
        self.albums_table = AlbumListView(parent=self)
        self.artists_table = ArtistListView(parent=self)
        self.videos_table = VideoListView(parent=self)
        self.playlists_table = PlaylistListView(parent=self)
        self.comments_table = CommentListView(parent=self)
        self.desc_widget = DescLabel(parent=self)

        self._tables.append(self.songs_table)
        self._tables.append(self.albums_table)
        self._tables.append(self.artists_table)
        self._tables.append(self.playlists_table)
        self._tables.append(self.videos_table)
        self._tables.append(self.comments_table)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.videos_table.play_video_needed.connect(
            lambda video: aio.create_task(self.play_video(video)))

        def goto_model(model):
            self._app.browser.goto(model=model)

        for signal in [self.songs_table.show_artist_needed,
                       self.songs_table.show_album_needed,
                       self.albums_table.show_album_needed,
                       self.artists_table.show_artist_needed,
                       self.playlists_table.show_playlist_needed,
                       ]:
            signal.connect(goto_model)

        self.toolbar.play_all_needed.connect(self.play_all)
        self.songs_table.add_to_playlist_needed.connect(self._add_songs_to_playlist)
        self.songs_table.about_to_show_menu.connect(self._songs_table_about_to_show_menu)
        self.songs_table.activated.connect(
            lambda index: aio.create_task(self._on_songs_table_activated(index)))

        self._setup_ui()

    def _setup_ui(self):
        self.current_table = None
        self.tabbar.hide()
        self.meta_widget.add_tabbar(self.tabbar)
        self.desc_widget.hide()

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.toolbar)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.desc_widget)
        for table in self._tables:
            self._layout.addWidget(table)
        self._layout.addStretch(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    @property
    def current_extra(self):
        return self._extra

    @current_extra.setter
    def current_extra(self, extra):
        """(alpha)"""
        if self._extra is not None:
            self._layout.removeWidget(self._extra)
            self._extra.deleteLater()
            del self._extra
        self._extra = extra
        if self._extra is not None:
            self._layout.insertWidget(1, self._extra)

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
            if table is self.artists_table:
                self.toolbar.artists_mode()
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
        self.current_extra = None
        # clean right_panel background image
        self._app.ui.right_panel.show_background_image(None)
        # disconnect songs_table signal
        signals = (
            self.tabbar.show_contributed_albums_needed,
            self.tabbar.show_albums_needed,
            self.tabbar.show_songs_needed,
            self.tabbar.show_artists_needed,
            self.tabbar.show_playlists_needed,
            self.tabbar.show_desc_needed,
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

    async def play_video(self, video):
        media = await aio.run_in_executor(None, lambda: video.media)
        self._app.player.play(media)

    def play_all(self):
        task_name = 'play-all'
        task_spec = self._app.task_mgr.get_or_create(task_name)

        def reader_readall_cb(task):
            with suppress(ProviderIOError, asyncio.CancelledError):
                songs = task.result()
                self._app.player.play_songs(songs=songs)
            self.toolbar.enter_state_playall_end()

        model = self.songs_table.model()
        # FIXME: think about a more elegant way
        reader = model.sourceModel()._reader
        if reader is not None:
            if reader.count is not None:
                task = task_spec.bind_blocking_io(reader.readall)
                self.toolbar.enter_state_playall_start()
                task.add_done_callback(reader_readall_cb)
                return
        songs = model.sourceModel().songs
        self._app.player.play_songs(songs=songs)

    async def show_model(self, model):
        model = self._app.library.cast_model_to_v1(model)
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
        warnings.warn('use readerer.show_songs please')
        renderer = Renderer()
        task = aio.create_task(self.set_renderer(renderer))
        if songs is not None:
            reader = wrap(songs)
        else:
            reader = songs_g
        task.add_done_callback(
            lambda _: renderer.show_songs(reader=reader))

    def show_albums_coll(self, albums_g):
        aio.create_task(self.set_renderer(AlbumsCollectionRenderer(albums_g)))

    def show_artists_coll(self, artists_g):
        aio.create_task(self.set_renderer(ArtistsCollectionRenderer(artists_g)))

    def show_player_playlist(self):
        aio.create_task(self.set_renderer(PlayerPlaylistRenderer()))

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def _add_songs_to_playlist(self, songs):
        for song in songs:
            self._app.playlist.add(song)

    def _songs_table_about_to_show_menu(self, ctx):
        add_action = ctx['add_action']
        models = ctx['models']
        if not models or models[0].meta.model_type != ModelType.song:
            return

        song = models[0]
        goto = self._app.browser.goto

        if self._app.library.check_flags_by_model(song, ProviderFlags.similar):
            add_action('相似歌曲', lambda *args: goto(model=song, path='/similar'))
        if self._app.library.check_flags_by_model(song, ProviderFlags.hot_comments):
            add_action('歌曲评论', lambda *args: goto(model=song, path='/hot_comments'))

    async def _on_songs_table_activated(self, index):
        """
        QTableView should have no IO operations.
        """
        from feeluown.widgets.songs import Column

        song = index.data(Qt.UserRole)
        if index.column() == Column.song:
            self.songs_table.play_song_needed.emit(song)
        else:
            try:
                song = await aio.run_in_executor(
                    None, self._app.library.song_upgrade, song)
            except NotSupported:
                assert ModelFlags.v2 & song.meta.flags
                self._app.show_msg('资源提供放不支持该功能')
                logger.info(f'provider:{song.source} does not support song_get')
                song.state = ModelState.cant_upgrade
            except (ProviderIOError, RequestException) as e:
                # FIXME: we should only catch ProviderIOError here,
                # but currently, some plugins such fuo-qqmusic may raise
                # requests.RequestException
                logger.exception('upgrade song failed')
                self._app.show_msg(f'请求失败: {str(e)}')
            else:
                if index.column() == Column.artist:
                    artists = song.artists
                    if artists:
                        if len(artists) > 1:
                            self.songs_table.show_artists_by_index(index)
                        else:
                            self.songs_table.show_artist_needed.emit(artists[0])
                elif index.column() == Column.album:
                    self.songs_table.show_album_needed.emit(song.album)
        model = self.songs_table.model()
        topleft = model.index(index.row(), 0)
        bottomright = model.index(index.row(), 4)
        model.dataChanged.emit(topleft, bottomright, [])
