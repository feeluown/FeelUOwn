import json
from http.cookies import SimpleCookie

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog, QTextEdit, QPushButton, \
    QVBoxLayout, QLabel
try:
    from feeluown.gui.widgets.weblogin import WebLoginView
except ImportError:
    has_webengine = False
else:
    has_webengine = True

from feeluown.utils import aio


class InvalidCookies(Exception):
    pass


class LoginDialog(QDialog):
    """Base class for login dialogs"""
    #: login succeed signal
    login_succeed = pyqtSignal()


class CookiesLoginDialog(LoginDialog):
    """

    CookiesLoginDialog provides a text edit area and a login button.
    User firstly fill in the text edit area with cookies. User can
    then click the login button. The `clicked` signal is connected to
    :meth:`.login`.

    Cookies can be in text or json format. User can copy cookies from
    web browser like Chrome or Firefox. Cookies copied from firefox are
    in json format and cookies copied from Chrome are in text format.

    Subclass MUST implement four methods.

    - :meth:`setup_user`
    - :meth:`user_from_cookies`
    - :meth:`load_user_cookies`
    - :meth:`dump_user_cookies`

    One usage example: feeluown-qqmusic.
    """

    def __init__(self, uri: str = None, required_cookies_fields=None):
        if has_webengine and uri and required_cookies_fields:
            use_webview = True
            flags = Qt.Window
        else:
            use_webview = False
            flags = Qt.Popup

        super().__init__(None, flags)
        self._use_webview = use_webview
        self._uri = uri
        self._required_cookies_fields = required_cookies_fields

        self.cookies_text_edit = QTextEdit(self)
        self.hint_label = QLabel(self)
        self.login_btn = QPushButton('登录', self)
        self.weblogin_btn = QPushButton('网页登录', self)

        self.hint_label.setTextFormat(Qt.RichText)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.cookies_text_edit)
        self._layout.addWidget(self.hint_label)
        self._layout.addWidget(self.login_btn)
        self._layout.addWidget(self.weblogin_btn)

        self.cookies_text_edit.setAcceptRichText(False)
        self.cookies_text_edit.setPlaceholderText(
            '请从浏览器中复制 Cookie：\n\n'
            'Chrome 复制的 cookie 格式类似：key1=value1; key2=value2\n\n'
            'Firefox 复制的 cookie 格式类似：{"key1": value1, "key1": value2}'
        )

        if self._use_webview is True:
            self.weblogin_btn.clicked.connect(self._start_web_login)
        else:
            # disable the button if feeluown does not support
            if uri and required_cookies_fields and not has_webengine:
                self.weblogin_btn.setEnabled(False)
            else:
                # hide the button if provider does not support
                self.weblogin_btn.hide()
        self.login_btn.clicked.connect(lambda: aio.create_task(self.login()))
        self.login_succeed.connect(self.hide)

    def _start_web_login(self):
        self._web_login = WebLoginView(self._uri, self._required_cookies_fields)
        self._web_login.succeed.connect(self._on_web_login_succeed)
        self._web_login.show()

    def _on_web_login_succeed(self, cookies):
        self.cookies_text_edit.setText(json.dumps(cookies, indent=2))
        self._web_login.close()
        del self._web_login
        aio.create_task(self.login())

    def _parse_json_cookies(self, text):
        try:
            return json.loads(text)
        except ValueError:
            return None

    def _parse_text_cookies(self, text):
        """
        cookies: uid=111; userAction=222;
        """
        cookie = SimpleCookie()
        cookie.load(text)
        cookie_dict = {}
        for _, morsel in cookie.items():
            cookie_dict[morsel.key] = morsel.value
        return cookie_dict or None

    def get_cookies(self):
        """Parse the content in text edit area

        :return: return None when the content is invalid
        :rtype: dict or None
        """
        # We assume users only use firefox and chrome. Cookies from firefox are
        # in json format. Cookies copied from chrome are in text format.
        parsers = (('json', self._parse_json_cookies),
                   ('text', self._parse_text_cookies))
        text = self.cookies_text_edit.toPlainText()
        cookies = None
        for name, parse in parsers:
            cookies = parse(text)
            if cookies is None:
                self.show_hint(f'使用 {name} 解析器解析失败，尝试下一种', color='orange')
            else:
                self.show_hint(f'使用 {name} 解析器解析成功')
                break
        return cookies

    def show_hint(self, text, color=None):
        """Show hint message on dialog

        :param string color: red for error, orange for warning,
            green for success
        """
        if color is None:
            color = ''
        self.hint_label.setText(f"<p style='color: {color}'>{text}</p>")

    async def login(self):
        """Login with cookies

        Read cookies that has been filled in and create a user from it.
        If succeed, the :attr:`.login_succeed` signal will be emit.
        If failed, show specific error message on the dialog based on
        the exception.
        """
        await self.login_with_cookies(self.get_cookies())

    async def login_with_cookies(self, cookies):
        try:
            user = await self.user_from_cookies(cookies)
        except InvalidCookies as e:
            self.show_hint(str(e), color='red')
        else:
            self.show_hint('保存用户信息到 FeelUOwn 数据目录')
            self.dump_user_cookies(user, cookies)
            self.setup_user(user)
            self.login_succeed.emit()

    def autologin(self):
        """Try to load user cookies and login with it

        Generally, you can call this method after dialog is shown.
        """
        cookies = self.load_user_cookies()
        if cookies is not None:
            self.show_hint('正在尝试加载已有用户...', color='green')
            self.cookies_text_edit.setText(json.dumps(cookies, indent=2))
            aio.create_task(self.login_with_cookies(cookies))

    def setup_user(self, user):
        """Setup user session

        :type user: feeluown.models.UserModel
        """
        raise NotImplementedError

    async def user_from_cookies(self, cookies):
        """Create a user model from cookies dict

        :type cookies: dict
        :rtype: feeluown.models.UserModel
        """
        raise NotImplementedError

    def load_user_cookies(self):
        """Load user cookies from somewhere

        Load the cookies that is dumped before. If the load processing failed,
        just return None.

        :return: cookies in dict format
        :rtype: dict or None
        """
        raise NotImplementedError

    def dump_user_cookies(self, user, cookies):
        """Dump user cookies to somewhere

        Generally, you can store the cookies in FeelUOwn data directory
        with specifical filename.

        :type user: feeluown.models.UserModel
        :type cookies: dict
        """
        raise NotImplementedError


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    widget = CookiesLoginDialog()
    widget.show()
    widget.show_hint('格式可能不正确', color='orange')
    app.exec()
