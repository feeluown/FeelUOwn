from feeluown.library import (
    V2SupportedModelTypes, AlbumModel,
    SupportsAlbumSongsReader, SupportsPlaylistRemoveSong,
    SupportsArtistAlbumsReader, SupportsArtistContributedAlbumsReader,
    SupportsPlaylistSongsReader, SupportsArtistSongsReader,
)
from feeluown.utils.aio import run_fn, run_afn
from feeluown.utils.reader import create_reader
from feeluown.library import ModelType, reverse

from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.widgets.songs import ColumnsMode
from .template import render_error_message


async def render(req, **kwargs):
    app = req.ctx['app']
    model = req.ctx['model']

    app.ui.page_view.set_body(app.ui.page_view.table_container)

    # FIXME: handle NotSupported exception here and in renderer.
    # FIXME: handle ProviderIOError and RequestException.
    if ModelType(model.meta.model_type) in V2SupportedModelTypes:
        if model.meta.model_type == ModelType.album:
            album = await run_fn(app.library.album_upgrade, model)
            tab_index = int(req.query.get('tab_index', 1))
            al_renderer = AlbumRenderer(album, tab_index)
            await app.ui.table_container.set_renderer(al_renderer)
        elif model.meta.model_type == ModelType.artist:
            artist = await run_fn(app.library.artist_upgrade, model)
            tab_index = int(req.query.get('tab_index', 1))
            ar_renderer = ArtistRenderer(artist, tab_index)
            await app.ui.table_container.set_renderer(ar_renderer)
        elif model.meta.model_type == ModelType.playlist:
            playlist = await run_fn(app.library.playlist_upgrade, model)
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
        self.meta_widget.title = await run_fn(lambda: artist.name)
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

            source = artist.source
            provider = self._app.library.get(source)
            if contributed is False and isinstance(provider, SupportsArtistAlbumsReader):
                reader = await run_fn(provider.artist_create_albums_rd, artist)
            elif isinstance(provider, SupportsArtistContributedAlbumsReader):
                reader = await run_fn(provider.artist_create_contributed_albums_rd, artist)  # noqa
            else:
                if contributed:
                    await render_error_message(self._app, '资源提供方不支持获取歌手贡献过的专辑')
                else:
                    await render_error_message(self._app, '资源提供方不支持获取歌手专辑')
                return
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
        provider = self._app.library.get(artist.source)
        if not isinstance(provider, SupportsArtistSongsReader):
            await render_error_message(self._app, '资源提供方不支持获取歌手歌曲')
            return

        async def cb():
            reader = await run_fn(provider.artist_create_songs_rd, artist)
            self.__show_songs(reader)

        await cb()
        self.tabbar.show_songs_needed.connect(lambda: run_afn(cb))

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
                    provider = self._app.library.get(album.source)
                    if isinstance(provider, SupportsAlbumSongsReader):
                        reader = await run_fn(provider.album_create_songs_rd, album)
                    else:
                        await render_error_message(self._app, '资源提供方不支持获取专辑歌曲')
                        return
            self.meta_widget.songs_count = reader.count
            self.show_songs(reader, columns_mode=ColumnsMode.album)

        # fetch cover and description
        cover = album.cover
        if cover:
            run_afn(self.show_cover, cover, reverse(album, '/cover'))


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
            run_afn(self.show_cover, playlist.cover, reverse(playlist) + '/cover')

        provider = self._app.library.get(self.playlist.source)
        if isinstance(provider, SupportsPlaylistRemoveSong):
            self.songs_table.remove_song_func = self.remove_song

    async def _show_songs(self):
        provider = self._app.library.get(self.playlist.source)
        if isinstance(provider, SupportsPlaylistSongsReader):
            reader = await run_fn(provider.playlist_create_songs_rd, self.playlist)
        else:
            await render_error_message(self._app, '资源提供方不支持获取歌单歌曲')
            return
        self.show_songs(reader=reader, show_count=True)

    def remove_song(self, song):

        async def do():
            provider = self._app.library.get(self.playlist.source)
            if await run_fn(provider.playlist_remove_song, self.playlist, song) is True:
                # Re-render songs table so that user can see that the song is removed.
                run_afn(self._show_songs)
                self._app.show_msg(f'移除歌曲 {song} 成功')
            else:
                self._app.show_msg(f'移除歌曲 {song} 失败')

        run_afn(do)
