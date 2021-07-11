from contextlib import suppress
from requests.exceptions import RequestException

from feeluown.excs import ProviderIOError
from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.models import ModelType, reverse

from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.page_containers.table import Renderer


async def render(req, **kwargs):
    app = req.ctx['app']
    model = req.ctx['model']

    if model.meta.model_type == ModelType.song:
        model = await aio.run_in_executor(None, app.library.song_upgrade, model)
        renderer = SongRenderer(model)
        await app.ui.table_container.set_renderer(renderer)
    elif model.meta.model_type == ModelType.artist:
        artist = app.library.cast_model_to_v1(model)
        tab_index = int(req.query.get('tab_index', 1))
        renderer = ArtistRenderer(artist, tab_index)
        await app.ui.table_container.set_renderer(renderer)
    elif model.meta.model_type == ModelType.album:
        album = app.library.cast_model_to_v1(model)
        tab_index = int(req.query.get('tab_index', 1))
        renderer = AlbumRenderer(album, tab_index)
        await app.ui.table_container.set_renderer(renderer)
    else:
        app.ui.right_panel.show_model(model)


class SongRenderer(Renderer):
    def __init__(self, song):
        self._song = song

    async def render(self):
        song = self._song
        self.meta_widget.title = f'{song.title}'
        self.meta_widget.subtitle = f'{song.artists_name} - {song.album_name}'
        self.meta_widget.show()

        brief_album = song.album
        album = self._app.library.cast_model_to_v1(brief_album)
        cover = await aio.run_in_executor(None, lambda: album.cover)
        if cover:
            await self.show_cover(cover, f'{reverse(album)}/cover')


class ModelTabBarRendererMixin(TabBarRendererMixin):
    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(model=self.model,
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
        self.meta_widget.show()

        self.render_tab_bar()

        if tab_index == 0:
            await self._show_desc()
        elif tab_index == 1:
            await self._show_songs()
        elif tab_index == 2:
            if artist.meta.allow_create_albums_g:
                self.toolbar.filter_albums_needed.connect(
                    lambda types: self.albums_table.model().filter_by_types(types))
                self.show_albums(artist.create_albums_g())
        elif tab_index == 3:
            if hasattr(artist, 'contributed_albums') and artist.contributed_albums:
                self.show_albums(artist.create_contributed_albums_g())

        # finally, we render cover
        cover = await aio.run_fn(lambda: artist.cover)
        if cover:
            await self.show_cover(cover,
                                  reverse(artist, '/cover'), as_background=True)

    async def _show_desc(self):
        with suppress(ProviderIOError, RequestException):
            desc = await aio.run_fn(lambda: self.model.desc)
            self.show_desc(desc)

    async def _show_songs(self):
        artist = self.model
        # fetch and render songs
        reader = None
        if artist.meta.allow_create_songs_g:
            reader = create_reader(artist.create_songs_g())
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(reader=create_reader(artist.create_songs_g()),
                                        show_count=True))
        else:
            songs = await aio.run_fn(lambda: artist.songs)
            reader = create_reader(songs)
            self.tabbar.show_songs_needed.connect(
                lambda: self.show_songs(reader=create_reader(songs), show_count=True))
        self.show_songs(reader=reader, show_count=True)


class AlbumRenderer(Renderer, ModelTabBarRendererMixin):
    def __init__(self, album, tab_index):
        self.model = album
        self.tab_index = tab_index
        self.tabs = [
            ('简介', ),
            ('歌曲', ),
        ]

    async def render(self):
        album = self.model
        tab_index = self.tab_index

        self.meta_widget.title = album.name_display
        self.meta_widget.creator = album.artists_name_display
        self.meta_widget.show()

        self.render_tab_bar()

        if tab_index == 0:
            aio.run_afn(self._show_desc)
        else:
            songs = await aio.run_fn(lambda: album.songs)
            self.meta_widget.songs_count = len(songs)
            self.show_songs(create_reader(songs))

        # fetch cover and description
        cover = await aio.run_fn(lambda: album.cover)
        if cover:
            aio.run_afn(self.show_cover, cover, reverse(album, '/cover'))

    async def _show_desc(self):
        with suppress(ProviderIOError):
            desc = await aio.run_fn(lambda: self.model.desc)
            self.show_desc(desc)
