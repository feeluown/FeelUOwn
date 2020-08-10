import json
from http.cookies import SimpleCookie

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog, QTextEdit, QPushButton, \
    QVBoxLayout, QLabel

from fuocore import aio


class InvalidCookies(Exception):
    pass


class LoginDialog(QDialog):

    login_succeed = pyqtSignal()


class CookiesLoginDialog(LoginDialog):
    """
    usage example: feeluown-qqmusic
    """
    def __init__(self):
        super().__init__(None, Qt.Popup)

        self.cookies_text_edit = QTextEdit(self)
        self.hint_label = QLabel(self)
        self.login_btn = QPushButton('登录', self)

        self.hint_label.setTextFormat(Qt.RichText)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.cookies_text_edit)
        self._layout.addWidget(self.hint_label)
        self._layout.addWidget(self.login_btn)

        self.cookies_text_edit.setAcceptRichText(False)
        self.cookies_text_edit.setPlaceholderText(
            '请从浏览器中复制 Cookie：\n\n'
            'Chrome 复制的 cookie 类似：uid=111; userAction=222\n\n'
            'Firefox 复制的 cookie 类似：{"uid": 111, "userAction": 222}'
        )

        self.login_btn.clicked.connect(lambda: aio.create_task(self.login()))
        self.login_succeed.connect(self.hide)

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
        if color is None:
            color = ''
        self.hint_label.setText(f"<p style='color: {color}'>{text}</p>")

    async def login(self):
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
        cookies = self.load_user_cookies()
        if cookies is not None:
            self.show_hint('正在尝试加载已有用户...', color='green')
            self.cookies_text_edit.setText(json.dumps(cookies, indent=2))
            aio.create_task(self.login_with_cookies(cookies))

    def setup_user(self, user):
        """setup user session

        :type user: fuocore.models.UserModel
        """
        raise NotImplementedError

    async def user_from_cookies(self, cookies):
        """

        :rtype UserModel:
        """
        raise NotImplementedError

    def load_user_cookies(self):
        """load user cookies from data file

        :return: cookies in dict format
        """
        raise NotImplementedError

    def dump_user_cookies(self, user, cookies):
        """

        :type user: fuocore.models.UserModel
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
