from urllib.parse import urlsplit, urlunsplit

from PyQt6.QtGui import QPainter

from feeluown.gui.drawers import ProxyIconDrawer, ProxyShieldBadgeDrawer
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.i18n import t
from feeluown.utils.utils import detect_proxy


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
    return "\n".join(f"{name}={url}" for name, url in sanitized.items())


def with_refresh_hint(text: str) -> str:
    return text + "\n\n" + t("proxy-click-to-refresh")


class NetworkStatusButton(SelfPaintAbstractSquareButton):
    def __init__(self, length=30, parent=None):
        super().__init__(length=length, padding=0.2, parent=parent)
        self._icon_drawer = ProxyIconDrawer(self.width(), self._padding)
        self._badge_drawer = ProxyShieldBadgeDrawer(self.width(), self._padding)
        self._has_proxy = False
        self.clicked.connect(self.refresh)
        self.refresh()

    def update_proxy_status(self, proxies: dict):
        self._has_proxy = bool(proxies)
        if proxies:
            self.setToolTip(
                with_refresh_hint(
                    t("proxy-detected", proxyInfo=format_proxies_for_display(proxies))
                )
            )
        else:
            self.setToolTip(with_refresh_hint(t("proxy-not-detected")))
        self.update()

    def refresh(self):
        self.update_proxy_status(detect_proxy())

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_round_bg_when_hover(painter)
        self._icon_drawer.draw(painter)

        if self._has_proxy is False:
            return

        self._badge_drawer.draw(painter, self.palette())
