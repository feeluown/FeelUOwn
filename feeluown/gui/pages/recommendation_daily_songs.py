from typing import TYPE_CHECKING

from feeluown.library import SupportsRecListDailySongs
from feeluown.gui.page_containers.table import TableContainer, Renderer
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.utils.aio import run_fn
from feeluown.utils.reader import create_reader
from feeluown.i18n import t
from .template import render_error_message


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render(req, **_):
    app: "GuiApp" = req.ctx["app"]
    pvd_ui = app.current_pvd_ui_mgr.get()
    if pvd_ui is None:
        return await render_error_message(app, t("provider-unknown-cannot-view"))

    provider = pvd_ui.provider

    scroll_area = ScrollArea()
    body = TableContainer(app, scroll_area)
    scroll_area.setWidget(body)
    app.ui.right_panel.set_body(scroll_area)
    if isinstance(provider, SupportsRecListDailySongs):
        songs = await run_fn(provider.rec_list_daily_songs)
        renderer = Renderer()
        await body.set_renderer(renderer)
        renderer.show_songs(create_reader(songs))
        renderer.meta_widget.show()
        renderer.meta_widget.title = t("recommended-daily-playlist")
