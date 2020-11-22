from typing import List
from urllib.parse import urlparse

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtNetwork import QNetworkCookie
from PyQt5.QtWebEngineCore import QWebEngineCookieStore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile


class WebLogin(QWebEngineView):
    succeed: pyqtSignal(dict)

    def __init__(self, uri: str, required_cookies: List[str], parent=None):
        """
        此工具类用于 QtWebEngine 自动化 Cookie 登录过程
        Example: QtWebEngine('https://y.qq.com', ['qqmusickey'])

        :param uri: 初始化登录地址 获取到的 Cookie 也会按照此地址筛选
        :rtype uri: str
        :param required_cookies: 必需包含的 Cookie key 当全部获取到将发送 succeed 信号并自动关闭
        :type required_cookies: List[str]
        :param parent:
        """
        super(WebLogin, self).__init__(parent)
        self.init_uri = uri
        profile = QWebEngineProfile.defaultProfile()
        cookie_store: QWebEngineCookieStore = profile.cookieStore()
        cookie_store.deleteAllCookies()
        cookie_store.cookieAdded.connect(self.cookie_added)
        cookie_store.cookieRemoved.connect(self.cookie_removed)
        self.saved_cookies = dict()
        self.required_cookies = required_cookies
        self.load(QUrl(uri))

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
        return urisegs.hostname.endswith(cookie_domain)

    def cookie_added(self, cookie: QNetworkCookie):
        if self.check_cookie_domain(cookie):
            self.saved_cookies[cookie.name().data().decode()] = cookie.value().data().decode()
            if self.required_cookies and len(set(self.required_cookies) & set(self.saved_cookies.keys())) == len(
                    set(self.required_cookies)):
                self.succeed.emit(self.saved_cookies)
                self.close()

    def cookie_removed(self, cookie: QNetworkCookie):
        if cookie.name().data().decode() in self.saved_cookies.keys():
            self.saved_cookies.pop(cookie.name().data().decode())
