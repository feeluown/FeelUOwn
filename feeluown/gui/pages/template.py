from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render_error_message(app: 'GuiApp', msg: str):
    label = QLabel(f"<span style='color: red;'>错误提示：{msg}<span>")
    label.setTextFormat(Qt.RichText)
    label.setAlignment(Qt.AlignCenter)
    app.ui.page_view.set_body(label)
