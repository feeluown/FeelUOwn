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
from feeluown.i18n import t
from .template import render_error_message


async def render(req, **kwargs):
    app: GuiApp = req.ctx["app"]
    ui = app.ui
    tab_index = int(req.query.get("tab_index", 0))
    pvd_ui = app.current_pvd_ui_mgr.get()
    if pvd_ui is None:
        return await render_error_message(app, "当前资源提供方未知，无法浏览该页面")

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
        self.meta_widget.title = "我的收藏"
        self.render_tab_bar()
        await self.render_models()

    async def render_models(self):
        # pylint: disable=too-many-branches
        _, mtype, show_handler = self.tabs[self.tab_index]
        media_type = ""
        reader = create_reader([])
        if mtype is ModelType.song:
            if isinstance(self._provider, SupportsCurrentUserFavSongsReader):
                reader = await run_fn(self._provider.current_user_fav_create_songs_rd)
            else:
                media_type = "track"
        elif mtype is ModelType.album:
            if isinstance(self._provider, SupportsCurrentUserFavAlbumsReader):
                reader = await run_fn(self._provider.current_user_fav_create_albums_rd)
            else:
                media_type = "album"
        elif mtype is ModelType.artist:
            if isinstance(self._provider, SupportsCurrentUserFavArtistsReader):
                reader = await run_fn(self._provider.current_user_fav_create_artists_rd)
            else:
                media_type = "singer"
        elif mtype is ModelType.playlist:
            if isinstance(self._provider, SupportsCurrentUserFavPlaylistsReader):
                reader = await run_fn(
                    self._provider.current_user_fav_create_playlists_rd
                )  # noqa
            else:
                media_type = "playlist"
        else:
            if isinstance(self._provider, SupportsCurrentUserFavVideosReader):
                reader = await run_fn(self._provider.current_user_fav_create_videos_rd)
            else:
                media_type = "video"
        if media_type:
            return await render_error_message(
                self._app,
                t(
                    "provider-missing-favorite",
                    providerName=self._provider.name,
                    mediaType=media_type,
                ),
            )
        else:
            show_handler(reader)

    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(page="/my_fav", query={"tab_index": tab_index})
