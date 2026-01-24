import logging
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

from feeluown.i18n import t

from requests import ConnectTimeout


if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)


class AlertManager:
    """Monitor app exceptions and send some alerts."""

    def __init__(self):
        # Some alerts handling rely on app and some are not.
        self._app: Optional["App"] = None

    def initialize(self, app: "App"):
        """"""
        self._app = app
        self._app.player.media_loading_failed.connect(
            self.on_media_loading_failed, aioqueue=True
        )

    def on_exception(self, e):
        if isinstance(e, ConnectTimeout):
            if e.request is not None:
                url = e.request.url
                hostname = urlparse(url).hostname
            else:
                hostname = "none"
            self.show_alert("connection-timeout", hostname=hostname)

    def on_media_loading_failed(self, *_):
        assert self._app is not None
        media = self._app.player.current_media
        if media and media.url:
            proxy = media.http_proxy if media.http_proxy else "none"
            hostname = urlparse(media.url).hostname
            msg = ()
            self.show_alert(msg, hostname=hostname, proxy=proxy)

    def show_alert(self, msg_id: str, **kwargs):
        logger.warning(t(msg_id, locale="en-US", **kwargs))
        self._app.show_msg(t(msg_id, **kwargs), timeout=2000)
