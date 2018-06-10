import hashlib
import json
import logging
import os

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot, QTime
from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView,
                             QMenu, QAction, QAbstractItemView,
                             QTableWidgetItem, QSizePolicy, QDialog, QFrame, QPushButton,
                             QScrollArea, QLabel)

from .consts import USER_PW_FILE

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    login_success = pyqtSignal([object])

    def __init__(self, verify_captcha, verify_userpw, create_user, parent=None):
        super().__init__(parent)

        self.verify_captcha = verify_captcha
        self.verify_userpw = verify_userpw
        self.create_user = create_user

        self.is_encrypted = False
        self.captcha_needed = False
        self.captcha_id = 0

        self.username_input = QLineEdit(self)
        self.pw_input = QLineEdit(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        # self.remember_checkbox = FCheckBox(self)
        self.captcha_label = QLabel(self)
        self.captcha_label.hide()
        self.captcha_input = QLineEdit(self)
        self.captcha_input.hide()
        self.hint_label = QLabel(self)
        self.ok_btn = QPushButton('登录', self)
        self._layout = QVBoxLayout(self)

        self.username_input.setPlaceholderText('网易邮箱或者手机号')
        self.pw_input.setPlaceholderText('密码')

        self.pw_input.textChanged.connect(self.dis_encrypt)
        self.ok_btn.clicked.connect(self.login)

        self.setFixedWidth(200)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.username_input)
        self._layout.addWidget(self.pw_input)
        self._layout.addWidget(self.captcha_label)
        self._layout.addWidget(self.captcha_input)
        self._layout.addWidget(self.hint_label)
        # self._layout.addWidget(self.remember_checkbox)
        self._layout.addWidget(self.ok_btn)

    def fill(self, data):
        self.username_input.setText(data['username'])
        self.pw_input.setText(data['password'])
        self.is_encrypted = True

    def show_hint(self, text):
        self.hint_label.setText(text)

    @property
    def data(self):
        username = self.username_input.text()
        pw = self.pw_input.text()
        if self.is_encrypted:
            password = pw
        else:
            password = hashlib.md5(pw.encode('utf-8')).hexdigest()
        d = dict(username=username, password=password)
        return d

    def captcha_verify(self, data):
        self.captcha_needed = True
        url = data['captcha_url']
        self.captcha_id = data['captcha_id']
        self.captcha_input.show()
        self.captcha_label.show()
        # FIXME: get pixmap from url
        # self._app.pixmap_from_url(url, self.captcha_label.setPixmap)

    def dis_encrypt(self, text):
        self.is_encrypted = False

    def login(self):
        if self.captcha_needed:
            captcha = str(self.captcha_input.text())
            captcha_id = self.captcha_id
            data = self.check_captcha(captcha_id, captcha)
            if data['code'] == 200:
                self.captcha_input.hide()
                self.captcha_label.hide()
            else:
                self.captcha_verify(data)

        user_data = self.data
        self.show_hint('正在登录...')
        data = self.verify_userpw(user_data['username'], user_data['password'])
        message = data['message']
        self.show_hint(message)
        if data['code'] == 200:
            self.save_user_pw(user_data)
            user = self.create_user(data)
            self.login_success.emit(user)
            self.hide()
        elif data['code'] == 415:
            self.captcha_verify(data)

    def save_user_pw(self, data):
        with open(USER_PW_FILE, 'w+') as f:
            if f.read() == '':
                d = dict()
            else:
                d = json.load(f)
            d['default'] = data['username']
            d[d['default']] = data
            json.dump(d, f, indent=4)

        logger.info('save username and password to %s' % USER_PW_FILE)

    def load_user_pw(self):
        if not os.path.exists(USER_PW_FILE):
            return
        with open(USER_PW_FILE, 'r') as f:
            d = json.load(f)
            data = d[d['default']]
        self.username_input.setText(data['username'])
        self.pw_input.setText(data['password'])
        self.is_encrypted = True

        logger.info('load username and password from %s' % USER_PW_FILE)
