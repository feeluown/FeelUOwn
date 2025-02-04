import logging
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

from requests import ConnectTimeout


if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)


class AlertManager:
    """Monitor app exceptions and send some alerts."""
    def __init__(self):
        # Some alerts handling rely on app and some are not.
        self._app: Optional['App'] = None

    def initialize(self, app: 'App'):
        """"""
        self._app = app
        self._app.player.media_loading_failed.connect(
            self.on_media_loading_failed, aioqueue=True)

    def on_exception(self, e):
        if isinstance(e, ConnectTimeout):
            if e.request is not None:
                url = e.request.url
                hostname = urlparse(url).hostname
            else:
                hostname = ''
            msg = f"链接'{hostname}'超时，请检查你的网络或者代理设置"
            self.show_alert(msg)

    def on_media_loading_failed(self, *_):
        assert self._app is not None
        media = self._app.player.current_media
        if media and media.url:
            proxy = f' {media.http_proxy}' if media.http_proxy else '空'
            hostname = urlparse(media.url).hostname
            msg = (f'无法播放来自 {hostname} 的资源（资源的 HTTP 代理为{proxy}）'
                   '（注：播放引擎无法使用系统代理）')
            self.show_alert(msg)

    def show_alert(self, alert):
        logger.warning(alert)
        self._app.show_msg(alert, timeout=2000)
