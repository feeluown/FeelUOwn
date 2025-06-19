import logging
from typing import List, Union
from urllib.parse import urlparse

from PyQt5.QtCore import pyqtSignal, QUrl, QRect
from PyQt5.QtNetwork import QNetworkCookie
from PyQt5.QtWebEngineCore import QWebEngineCookieStore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, \
    QWebEnginePage
from PyQt5.QtWidgets import QApplication, QDesktopWidget


logger = logging.getLogger(__name__)


class NoOutputWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        pass


class WebLoginView(QWebEngineView):
    succeed = pyqtSignal(dict)

    def __init__(self, uri: str, required_cookies: List[Union[str, List[str]]],
                 parent=None):
        """
        This utility class is used for automating the cookie login process.
        Example: QtWebEngine('https://y.xx.com', ['xxmusic_key'])

        :param uri: The initial login URL.
        :param required_cookies: List of required Cookie keys. When all are obtained,
            the succeed signal will be emitted and the window will close automatically.
            You can also use a list of lists, for example:
               [['xx_key', 'xx_wxuin'], ['xx_key', 'xx_uin]]
        :param parent:
        """
        super().__init__(parent)
        self.set_pos()
        self.init_uri = uri
        profile = QWebEngineProfile.defaultProfile()
        cookie_store: QWebEngineCookieStore = profile.cookieStore()
        cookie_store.deleteAllCookies()
        cookie_store.cookieAdded.connect(self.cookie_added)
        cookie_store.cookieRemoved.connect(self.cookie_removed)
        self.saved_cookies = dict()  # type: ignore
        self.required_cookies_options = []
        if required_cookies:
            if isinstance(required_cookies[0], list):
                for option in required_cookies:
                    self.required_cookies_options.append(option)
            else:
                self.required_cookies_options.append(required_cookies)
        self.setPage(NoOutputWebPage(self))
        self.load(QUrl(uri))

    def set_pos(self):
        desktop: QDesktopWidget = QApplication.desktop()
        screen = desktop.screenNumber(QApplication.desktop().cursor().pos())
        geo: QRect = desktop.availableGeometry(screen)
        self.setFixedWidth(int(geo.width() / 1.5))
        self.setFixedHeight(int(geo.height() / 1.5))
        frame: QRect = self.frameGeometry()
        frame.moveCenter(geo.center())
        self.move(frame.topLeft())

    def check_cookie_domain(self, cookie: QNetworkCookie):
        """
        检查 Cookie 的域名
        :param cookie: Cookie
        :type cookie: QNetworkCookie
        :return: 是否匹配域名
        :rtype: bool
        """
        cookie_domain = cookie.domain().lstrip('.')
        urisegs = urlparse(self.init_uri)
        if urisegs.hostname is not None:
            return urisegs.hostname.endswith(cookie_domain)
        return False

    def cookie_added(self, cookie: QNetworkCookie):
        if self.check_cookie_domain(cookie):
            name = cookie.name().data().decode()
            value = cookie.value().data().decode()
            self.saved_cookies[name] = value
            for required_cookies in self.required_cookies_options:
                ok = True
                one_ok = False
                for _name in required_cookies:
                    if _name not in self.saved_cookies:
                        ok = False
                        if one_ok is True:  # log for debugging
                            logger.debug(
                                f"not enough cookies for login, "
                                f"required: {required_cookies}, "
                                f"not satisfied: {_name}"
                            )
                        break
                    one_ok = True

                if ok is True:
                    logger.debug(
                        f"enough cookies for login, "
                        f"required: {self.required_cookies_options}, "
                        f"acture: {self.saved_cookies}"
                    )
                    self.succeed.emit(self.saved_cookies)
                    break

    def cookie_removed(self, cookie: QNetworkCookie):
        if cookie.name().data().decode() in self.saved_cookies.keys():
            self.saved_cookies.pop(cookie.name().data().decode())


if __name__ == '__main__':
    app = QApplication([])
    widget = WebLoginView("xxx", ['xxx_key'])
    widget.show()
    app.exec()
