import hashlib
import logging

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QDialog,
    QPushButton,
    QLabel,
    QDialogButtonBox,
)

from fuocore.xiami.api import api
from fuocore.xiami.schemas import UserSchema

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """虾米音乐登录对话框"""

    login_success = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._label = QLabel(self)
        self.username_input = QLineEdit(self)
        self.pw_input = QLineEdit(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        self._btn_box = QDialogButtonBox(self)
        self._ok_btn = QDialogButtonBox.Ok
        self._setup_ui()

        self.setWindowTitle('虾米账号密码登录')

        self._btn_box.clicked.connect(self.do_verify)

    def _setup_ui(self):
        self._btn_box.addButton(self._ok_btn)
        self._label.hide()

        self._layout = QFormLayout(self)
        self._layout.addRow('邮箱/手机号：', self.username_input)
        self._layout.addRow('密码：', self.pw_input)
        self._layout.addRow(self._label)
        self._layout.addRow(self._btn_box)

    def show_msg(self, msg, error=False):
        """显示提示信息"""
        self._label.show()
        self._label.setTextFormat(Qt.RichText)
        if error:
            color = 'red'
        else:
            color = 'green'
        self._label.setText('<span style="color: {};">{}</span>'
                            .format(color, msg))

    def do_verify(self):
        """校验用户名和密码，成功则发送信号"""
        username = self.username_input.text()
        password = self.pw_input.text()
        pw_md5digest = hashlib.md5(password.encode('utf-8')).hexdigest()
        rv = api.login(username, pw_md5digest)
        code, msg = rv['ret'][0].split('::')
        is_success = code == 'SUCCESS'
        self.show_msg(msg, error=(not is_success))
        if is_success:
            data = rv['data']['data']
            schema = UserSchema(strict=True)
            user, _ = schema.load(data)
            self.login_success.emit(user)
            self.close()
