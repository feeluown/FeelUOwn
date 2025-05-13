import asyncio
import logging
import warnings
from contextlib import suppress
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPalette
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QApplication, QWidget
from requests.exceptions import RequestException  # type: ignore[import]

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.media import Media, MediaType
from feeluown.excs import ProviderIOError
from feeluown.library import ModelState, ModelType, ModelNotFound

from feeluown.gui.helpers import BgTransparentMixin, \
    disconnect_slots_if_has, fetch_cover_wrapper
from feeluown.gui.components import SongMenuInitializer
from feeluown.gui.widgets.img_card_list import ImgCardListView
from feeluown.gui.widgets.img_card_list import (
    AlbumCardListModel, AlbumCardListView, AlbumFilterProxyModel, AlbumCardListDelegate,
    ArtistCardListModel, ArtistCardListView, ArtistFilterProxyModel,
    VideoCardListModel, VideoCardListView, VideoFilterProxyModel, VideoCardListDelegate,
    PlaylistCardListModel, PlaylistCardListView, PlaylistFilterProxyModel,
    PlaylistCardListDelegate, ArtistCardListDelegate,
)
from feeluown.gui.widgets.songs import ColumnsMode, SongsTableModel, SongsTableView, \
    SongFilterProxyModel
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.gui.widgets.meta import TableMetaWidget
from feeluown.gui.widgets.table_toolbar import SongsTableToolbar
from feeluown.gui.widgets.tabbar import TableTabBarV2

logger = logging.getLogger(__name__)


class Renderer:
    async def setUp(self, container):
        # pylint: disable=attribute-defined-outside-init
        self.container = container
        self.meta_widget = container.meta_widget
        self.desc_widget = container.desc_widget
        self.toolbar = container.toolbar
        self.tabbar = container.tabbar
        self.songs_table: SongsTableView = container.songs_table
        self.albums_table = container.albums_table
        self.artists_table = container.artists_table
        self.videos_table = container.videos_table
        self.playlists_table = container.playlists_table
        self.comments_table = container.comments_table
        # pylint: disable=protected-access
        self._app = container._app

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
                self.meta_widget.set_cover_image(None)
                self._app.ui.right_panel.show_background_image(pixmap)
            else:
                self._app.ui.right_panel.show_background_image(None)
                self.meta_widget.set_cover_image(img)
            self._app.ui.table_container.updateGeometry()

    def show_albums(self, reader):
        self._show_model_with_cover(reader,
                                    self.albums_table,
                                    AlbumCardListModel,
                                    AlbumFilterProxyModel)

    def show_artists(self, reader):
        self._show_model_with_cover(reader,
                                    self.artists_table,
                                    ArtistCardListModel,
                                    ArtistFilterProxyModel)

    def show_videos(self, reader):
        self._show_model_with_cover(reader,
                                    self.videos_table,
                                    VideoCardListModel,
                                    VideoFilterProxyModel)

    def show_playlists(self, reader):
        self._show_model_with_cover(reader,
                                    self.playlists_table,
                                    PlaylistCardListModel,
                                    PlaylistFilterProxyModel)

    def _show_model_with_cover(self, reader, table, model_cls, filter_model_cls):
        self.container.current_table = table
        filter_model = filter_model_cls()
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = model_cls(reader,
                          fetch_cover_wrapper(self._app),
                          source_name_map=source_name_map)
        filter_model.setSourceModel(model)
        table.setModel(filter_model)
        table.scrollToTop()
        disconnect_slots_if_has(self._app.ui.magicbox.filter_text_changed)
        self._app.ui.magicbox.filter_text_changed.connect(filter_model.filter_by_text)

    def show_songs(self, reader, show_count=False, columns_mode=ColumnsMode.normal):
        """
        .. versionadded: v3.8.5
           The *hide_columns* parameter.
        """
        reader = wrap(reader)
        if show_count:
            count = reader.count
            self.meta_widget.songs_count = -1 if count is None else count
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = SongsTableModel(
            source_name_map=source_name_map,
            reader=reader,
            parent=self.songs_table,
        )
        self.show_songs_by_model(model, columns_mode=columns_mode)

    def show_songs_by_model(self, model, columns_mode=ColumnsMode.normal):
        self.container.current_table = self.songs_table
        self.toolbar.show()
        filter_model = SongFilterProxyModel(self.songs_table)
        filter_model.setSourceModel(model)
        self.songs_table.setModel(filter_model)
        self.songs_table.scrollToTop()
        self.songs_table.set_columns_mode(columns_mode)
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

    def _get_source_alias(self, source):
        provider = self._app.library.get(source)
        return provider.name if provider is not None else ''


class SongsCollectionRenderer(Renderer):
    def __init__(self, collection):
        self.collection = collection

    async def render(self):
        collection = self.collection
        self.meta_widget.show()
        self.meta_widget.title = collection.name
        self.meta_widget.updated_at = collection.updated_at
        self.meta_widget.created_at = collection.created_at
        self.songs_table.remove_song_func = self.remove_song
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

    def remove_song(self, song):
        self.collection.remove(song)
        # Re-render songs table so that user can see that the song is removed.
        self._show_songs()


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


class DescLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setContentsMargins(30, 15, 30, 10)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.palette().setColor(QPalette.Background, self.palette().color(QPalette.Base))


class TableContainer(QFrame, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._renderer = None
        self._table = None  # current visible table
        self._tables: List[QWidget] = []

        self._extra = None
        self.toolbar = SongsTableToolbar()
        self.tabbar = TableTabBarV2()
        self.meta_widget = TableMetaWidget(parent=self)
        self.songs_table = SongsTableView(app=self._app, parent=self)
        self.albums_table = AlbumCardListView(parent=self)
        self.albums_table.setItemDelegate(
            AlbumCardListDelegate(self.albums_table, img_min_width=120))
        self.artists_table = ArtistCardListView(parent=self)
        self.artists_table.setItemDelegate(ArtistCardListDelegate(self.artists_table))
        self.videos_table = VideoCardListView(parent=self)
        self.videos_table.setItemDelegate(VideoCardListDelegate(self.videos_table))
        self.playlists_table = PlaylistCardListView(parent=self)
        self.playlists_table.setItemDelegate(
            PlaylistCardListDelegate(self.playlists_table))
        self.comments_table = CommentListView(parent=self)
        self.desc_widget = DescLabel(parent=self)

        self._tables.append(self.songs_table)
        self._tables.append(self.albums_table)
        self._tables.append(self.artists_table)
        self._tables.append(self.playlists_table)
        self._tables.append(self.videos_table)
        self._tables.append(self.comments_table)

        self.songs_table.play_song_needed.connect(
            lambda song: aio.run_afn(self.play_song, song))
        self.videos_table.play_video_needed.connect(
            self._app.playlist.play_model)

        def goto_model(model):
            self._app.browser.goto(model=model)

        for signal in [self.songs_table.show_artist_needed,
                       self.songs_table.show_album_needed,
                       self.albums_table.show_album_needed,
                       self.artists_table.show_artist_needed,
                       self.playlists_table.show_playlist_needed,
                       ]:
            signal.connect(goto_model)

        self.toolbar.play_all_needed.connect(
            lambda: aio.run_afn(self.play_all))
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
        self._v_layout = QVBoxLayout()

        self._v_layout.addWidget(self.meta_widget)
        self._v_layout.addSpacing(15)
        self._v_layout.addWidget(self.toolbar)
        self._v_layout.addWidget(self.desc_widget)

        # Since QTableView has a margin on the left and right(see SongsTableDelegate),
        # so set the v_layout left margin to same value(0) to align widgets.
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._v_layout)
        for table in self._tables:
            self._layout.addWidget(table)
        self._layout.addStretch(0)
        self._layout.setContentsMargins(20, 0, 20, 0)
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
        if isinstance(self._table, ImgCardListView):
            self._table.setModel(None)
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
        self.tabbar.restore_default()
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
        self._app.playlist.play_model(song)

    async def play_all(self):
        task_name = 'play-all'
        task_spec = self._app.task_mgr.get_or_create(task_name)
        model = self.songs_table.model()
        assert isinstance(model, SongFilterProxyModel)
        source_model = model.sourceModel()
        assert isinstance(source_model, SongsTableModel)
        # FIXME: think about a more elegant way to get reader.
        reader = source_model.reader
        if reader is not None and reader.count is not None:
            self.toolbar.enter_state_playall_start()
            with suppress(ProviderIOError, asyncio.CancelledError):
                songs = await task_spec.bind_blocking_io(reader.readall)
                self._app.playlist.set_models(songs)
                task = self._app.playlist.next()
                if task is not None:
                    await task
                    self._app.player.resume()
            self.toolbar.enter_state_playall_end()
            return
        assert False, 'The play_all_btn should be hide in this page'

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
        warnings.warn('use readerer.show_albums please')
        aio.create_task(self.set_renderer(AlbumsCollectionRenderer(albums_g)))

    def show_artists_coll(self, artists_g):
        warnings.warn('use readerer.show_artists please')
        aio.create_task(self.set_renderer(ArtistsCollectionRenderer(artists_g)))

    def _add_songs_to_playlist(self, songs):
        for song in songs:
            self._app.playlist.add(song)

    def _songs_table_about_to_show_menu(self, ctx):
        models = ctx['models']
        if not models or models[0].meta.model_type != ModelType.song:
            return

        menu = ctx['menu']
        song = models[0]
        menu.addSeparator()
        SongMenuInitializer(self._app, song).apply(menu)

    async def _on_songs_table_activated(self, index):
        """
        QTableView should have no IO operations.
        """
        from feeluown.gui.widgets.songs import Column

        song = index.data(Qt.UserRole)
        if index.column() == Column.song:
            # .. versionadded:: 3.7.11
            #    Reset playlist with songs in table if Alt key is pressed.
            if QApplication.keyboardModifiers() & Qt.AltModifier:
                model = self.songs_table.model()
                if isinstance(model, SongFilterProxyModel):
                    model = model.sourceModel()
                    if isinstance(model, SongsTableModel):
                        reader = model.reader
                        songs = await aio.run_fn(reader.readall)
                        self._app.playlist.clear()
                        self._app.playlist.set_models(songs)
            self._app.playlist.play_model(song)
        else:
            try:
                song = await aio.run_in_executor(
                    None, self._app.library.song_upgrade, song)
            except ModelNotFound as e:
                self._app.show_msg(f'资源提供方不支持该功能: {str(e)}')
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
