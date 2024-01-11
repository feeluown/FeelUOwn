from feeluown.app.gui_app import GuiApp
from feeluown.library import ModelType
from feeluown.utils.aio import run_fn
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.library import (
    SupportsCurrentUserFavSongsReader,
    SupportsCurrentUserFavAlbumsReader,
    SupportsCurrentUserFavArtistsReader,
    SupportsCurrentUserFavPlaylistsReader,
    SupportsCurrentUserFavVideosReader,
)
from feeluown.utils.reader import create_reader
from .template import render_error_message


async def render(req, **kwargs):
    app: GuiApp = req.ctx['app']
    ui = app.ui
    tab_index = int(req.query.get('tab_index', 0))
    pvd_ui = app.current_pvd_ui_mgr.get()
    if pvd_ui is None:
        return await render_error_message(app, '当前资源提供方未知，无法浏览该页面')

    ui.right_panel.set_body(ui.right_panel.scrollarea)
    table_container = ui.right_panel.table_container
    renderer = MyFavRenderer(app, tab_index, pvd_ui.provider)
    await table_container.set_renderer(renderer)


class MyFavRenderer(Renderer, TabBarRendererMixin):
    def __init__(self, app, tab_index, provider):
        self._app = app
        self._provider = provider
        self.tab_index = tab_index
        self.tabs = self.default_tabs()

    async def render(self):
        self.meta_widget.show()
        self.meta_widget.title = '我的收藏'
        self.render_tab_bar()
        await self.render_models()

    async def render_models(self):
        # pylint: disable=too-many-branches
        _, mtype, show_handler = self.tabs[self.tab_index]
        err = ''
        reader = create_reader([])
        if mtype is ModelType.song:
            if isinstance(self._provider, SupportsCurrentUserFavSongsReader):
                reader = await run_fn(self._provider.current_user_fav_create_songs_rd)
            else:
                err = '收藏的歌曲'
        elif mtype is ModelType.album:
            if isinstance(self._provider, SupportsCurrentUserFavAlbumsReader):
                reader = await run_fn(self._provider.current_user_fav_create_albums_rd)
            else:
                err = '收藏的专辑'
        elif mtype is ModelType.artist:
            if isinstance(self._provider, SupportsCurrentUserFavArtistsReader):
                reader = await run_fn(self._provider.current_user_fav_create_artists_rd)
            else:
                err = '收藏的歌手'
        elif mtype is ModelType.playlist:
            if isinstance(self._provider, SupportsCurrentUserFavPlaylistsReader):
                reader = await run_fn(self._provider.current_user_fav_create_playlists_rd)  # noqa
            else:
                err = '收藏的歌单'
        else:
            if isinstance(self._provider, SupportsCurrentUserFavVideosReader):
                reader = await run_fn(self._provider.current_user_fav_create_videos_rd)
            else:
                err = '收藏的视频'
        if err:
            return await render_error_message(
                self._app,
                f'当前资源提供方（{self._provider.name}）不支持获取 {err}'
            )
        else:
            show_handler(reader)

    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(page='/my_fav', query={'tab_index': tab_index})
