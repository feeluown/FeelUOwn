from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.widgets.labels import MessageLabel

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render_error_message(app: "GuiApp", msg: str):
    label = MessageLabel(msg, MessageLabel.ERROR)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    app.ui.page_view.set_body(label)


async def render_scroll_area_view(req, view_cls):
    app: "GuiApp" = req.ctx["app"]
    view = view_cls(app)
    # Keep page rendering behavior consistent across pages that need a
    # scrollable body with custom widgets.
    scroll_area = ScrollArea()
    scroll_area.setWidget(view)
    app.ui.right_panel.set_body(scroll_area)
    await view.render()
