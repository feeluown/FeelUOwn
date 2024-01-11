from feeluown.library import V2SupportedModelTypes, AlbumModel, NotSupported
from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.library import ModelType, reverse

from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.widgets.songs import ColumnsMode


async def render(req, **kwargs):
    app = req.ctx['app']
    model = req.ctx['model']

    app.ui.page_view.set_body(app.ui.page_view.table_container)

    # FIXME: handle NotSupported exception here and in renderer.
    # FIXME: handle ProviderIOError and RequestException.
    if ModelType(model.meta.model_type) in V2SupportedModelTypes:
        if model.meta.model_type == ModelType.album:
            album = await aio.run_fn(app.library.album_upgrade, model)
            tab_index = int(req.query.get('tab_index', 1))
            al_renderer = AlbumRenderer(album, tab_index)
            await app.ui.table_container.set_renderer(al_renderer)
        elif model.meta.model_type == ModelType.artist:
            artist = await aio.run_fn(app.library.artist_upgrade, model)
            tab_index = int(req.query.get('tab_index', 1))
            ar_renderer = ArtistRenderer(artist, tab_index)
            await app.ui.table_container.set_renderer(ar_renderer)
        elif model.meta.model_type == ModelType.playlist:
            playlist = await aio.run_fn(app.library.playlist_upgrade, model)
            pl_renderer = PlaylistRenderer(playlist)
            await app.ui.table_container.set_renderer(pl_renderer)
        else:
            assert False, "this should not be called"
            await app.ui.table_container.set_renderer(None)
    else:
        assert False, "can't render this type of model"


class ModelTabBarRendererMixin(TabBarRendererMixin):
    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(model=self.model,  # type: ignore[attr-defined]
                               query={'tab_index': tab_index})


class ArtistRenderer(Renderer, ModelTabBarRendererMixin):
    def __init__(self, artist, tab_index):
        self.model = artist
        self.tab_index = tab_index
        self.tabs = [
            ('简介', ),
            ('歌曲', ),
            ('专辑', ),
            ('参与作品', ),
        ]

    async def render(self):
        artist = self.model
        tab_index = self.tab_index

        # fetch and render basic metadata
        self.meta_widget.title = await aio.run_fn(lambda: artist.name)
        self.meta_widget.source = self._get_source_alias(artist.source)
        self.meta_widget.show()

        self.render_tab_bar()

        if tab_index == 0:
            self.show_desc(self.model.description)
        elif tab_index == 1:
            await self._show_songs()
        elif tab_index in (2, 3):
            contributed = tab_index == 3
            self.toolbar.filter_albums_needed.connect(
                lambda types: self.albums_table.model().filter_by_types(types))
            reader = await aio.run_fn(
                self._app.library.artist_create_albums_rd, artist, contributed)
            self.toolbar.show()
            self.show_albums(reader)

        # finally, we render cover
        cover = artist.pic_url
        if cover:
            await self.show_cover(cover,
                                  reverse(artist) + '/cover',
                                  as_background=True)

    async def _show_songs(self):
        artist = self.model
        reader = await aio.run_fn(self._app.library.artist_create_songs_rd, artist)

        async def cb():
            reader = await aio.run_fn(self._app.library.artist_create_songs_rd, artist)
            self.__show_songs(reader)

        self.tabbar.show_songs_needed.connect(lambda: aio.run_afn(cb))
        self.__show_songs(reader)

    def __show_songs(self, reader):
        self.show_songs(reader=reader,
                        show_count=True,
                        columns_mode=ColumnsMode.artist)


class AlbumRenderer(Renderer, ModelTabBarRendererMixin):
    def __init__(self, album, tab_index):
        self.model = album
        self.tab_index = tab_index
        self.tabs = [
            ('简介', ),
            ('歌曲', ),
        ]

    async def render(self):
        album: AlbumModel = self.model
        tab_index = self.tab_index

        if album.released:
            self.meta_widget.released_at = album.released

        self.meta_widget.title = album.name
        self.meta_widget.creator = album.artists_name
        self.meta_widget.source = self._get_source_alias(album.source)
        self.meta_widget.show()

        self.render_tab_bar()

        if tab_index == 0:
            self.show_desc(self.model.description)
        else:
            if album.songs:
                reader = create_reader(album.songs)
            else:
                if album.song_count == 0:
                    reader = create_reader([])
                else:
                    try:
                        reader = await aio.run_fn(
                            self._app.library.album_create_songs_rd, album)
                    except NotSupported as e:
                        self._app.show_msg(str(e))
                        reader = create_reader([])
            self.meta_widget.songs_count = reader.count
            self.show_songs(reader, columns_mode=ColumnsMode.album)

        # fetch cover and description
        cover = album.cover
        if cover:
            aio.run_afn(self.show_cover, cover, reverse(album, '/cover'))


class PlaylistRenderer(Renderer):
    def __init__(self, playlist):
        self.playlist = playlist

    async def render(self):
        playlist = self.playlist

        # show playlist title
        self.meta_widget.show()
        self.meta_widget.title = playlist.name
        self.meta_widget.source = self._get_source_alias(playlist.source)

        await self._show_songs()

        # show playlist cover
        if playlist.cover:
            aio.create_task(
                self.show_cover(playlist.cover,
                                reverse(playlist) + '/cover'))

        self.songs_table.remove_song_func = self.remove_song

    async def _show_songs(self):
        reader = await aio.run_fn(self._app.library.playlist_create_songs_rd,
                                  self.playlist)
        self.show_songs(reader=reader, show_count=True)

    def remove_song(self, song):
        # FIXME: this may block the whole app.
        if self._app.library.playlist_remove_song(self.playlist, song) is True:
            # Re-render songs table so that user can see that the song is removed.
            aio.run_afn(self._show_songs)
        else:
            self._app.show_msg('移除歌曲失败')
