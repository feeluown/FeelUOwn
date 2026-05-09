from typing import TYPE_CHECKING

from feeluown.gui.widgets import EmojiButton
from feeluown.i18n import t
from feeluown.utils.utils import format_proxies_for_display

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class ProxyStatusButton(EmojiButton):
    def __init__(self, app: "GuiApp", *args, **kwargs):
        super().__init__("🌐", "", *args, **kwargs)
        self._app = app
        self.update_proxies({})

    def update_proxies(self, proxies: dict):
        if proxies:
            self.setToolTip(
                t("proxy-detected", proxy_info=format_proxies_for_display(proxies))
            )
        else:
            self.setToolTip(t("proxy-not-detected"))
