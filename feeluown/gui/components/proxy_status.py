from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from feeluown.gui.widgets import EmojiButton
from feeluown.i18n import t

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


def sanitize_proxy_url(url: str) -> str:
    """Remove userinfo from a proxy URL before display."""
    split = urlsplit(url)
    netloc = split.netloc
    if "@" not in netloc:
        return url
    netloc = netloc.rsplit("@", 1)[-1]
    return urlunsplit((split.scheme, netloc, split.path, split.query, split.fragment))


def sanitize_proxies(proxies: dict) -> dict:
    return {name: sanitize_proxy_url(url) for name, url in proxies.items()}


def format_proxies_for_display(proxies: dict) -> str:
    sanitized = sanitize_proxies(proxies)
    return ", ".join(f"{name}={url}" for name, url in sanitized.items())


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
