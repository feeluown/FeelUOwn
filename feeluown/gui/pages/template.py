from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

from feeluown.gui.widgets.labels import MessageLabel

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render_error_message(app: "GuiApp", msg: str):
    label = MessageLabel(msg, MessageLabel.ERROR)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    app.ui.page_view.set_body(label)
