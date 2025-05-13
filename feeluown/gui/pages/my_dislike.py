from feeluown.app.gui_app import GuiApp
from feeluown.library import ModelType
from feeluown.utils.aio import run_fn, run_afn
from feeluown.gui.page_containers.table import Renderer, TableContainer
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.library import (
    SupportsCurrentUserDislikeSongsReader,
    SupportsCurrentUserDislikeRemoveSong,
)
from feeluown.utils.reader import create_reader
from .template import render_error_message


async def render(req, **kwargs):
    app: GuiApp = req.ctx['app']
    tab_index = int(req.query.get('tab_index', 0))
    pvd_ui = app.current_pvd_ui_mgr.get()
    if pvd_ui is None:
        return await render_error_message(app, '当前资源提供方未知，无法浏览该页面')

    scroll_area = ScrollArea()
    # it should not use TableContainer.songs_table to show
    # the dislike song list. For example, the TableContainer.songs_table
    # has a fixed context menu, which is not suitable for the dislike song list.
    # TODO: Maybe design a widget to show the dislike list.
    table_container = TableContainer(app, scroll_area)
    scroll_area.setWidget(table_container)
    app.ui.right_panel.set_body(scroll_area)
    renderer = DislikeRenderer(app, tab_index, pvd_ui.provider)
    await table_container.set_renderer(renderer)


class DislikeRenderer(Renderer, TabBarRendererMixin):
    def __init__(self, app, tab_index, provider):
        self._app = app
        self._provider = provider
        self.tab_index = tab_index
        self.tabs = self.default_tabs()[:1]

    async def render(self):
        self.meta_widget.show()
        self.meta_widget.title = '音乐黑名单'
        self.render_tab_bar()
        await self.render_models()

    async def dislike_remove_song(self, song):
        await run_fn(self._provider.current_user_dislike_remove_song, song)
        # Workaround: re-render to refresh the page
        await self.render()

    async def render_models(self):
        _, mtype, show_handler = self.tabs[self.tab_index]
        err = ''
        reader = create_reader([])
        if mtype is ModelType.song:
            if isinstance(self._provider, SupportsCurrentUserDislikeSongsReader):
                reader = await run_fn(self._provider.current_user_dislike_create_songs_rd)  # noqa
            else:
                err = '不喜欢的歌曲'
            if isinstance(self._provider, SupportsCurrentUserDislikeRemoveSong):
                self.songs_table.remove_song_func = \
                    lambda song: run_afn(self.dislike_remove_song, song)
        else:
            err = '未知类型资源'

        if err:
            return await render_error_message(
                self._app,
                f'当前资源提供方（{self._provider.name}）不支持展示 {err} 的黑名单'
            )
        else:
            show_handler(reader)
        # Do not show playall button.
        self.toolbar.hide()

    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(page='/my_dislike', query={'tab_index': tab_index})
