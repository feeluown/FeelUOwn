import asyncio
import hashlib
import logging

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot, QTime
from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView,
                             QMenu, QAction, QAbstractItemView,
                             QTableWidgetItem, QSizePolicy, QDialog, QFrame, QPushButton,
                             QScrollArea, QLabel)
from fuocore.models import PlaylistModel, SongModel

from feeluown.utils import set_alpha, parse_ms
from .model import NUserModel

logger = logging.getLogger(__name__)


class LineInput(QLineEdit):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('line_input')
        self.set_theme_style()

    def set_theme_style(self):
        pass


class LoginDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.is_encrypted = False
        self.captcha_needed = False
        self.captcha_id = 0

        self.username_input = LineInput(self)
        self.pw_input = LineInput(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        # self.remember_checkbox = FCheckBox(self)
        self.captcha_label = QLabel(self)
        self.captcha_label.hide()
        self.captcha_input = LineInput(self)
        self.captcha_input.hide()
        self.hint_label = QLabel(self)
        self.ok_btn = QPushButton('登录', self)
        self._layout = QVBoxLayout(self)

        self.username_input.setPlaceholderText('网易邮箱或者手机号')
        self.pw_input.setPlaceholderText('密码')

        self.setObjectName('login_dialog')
        self.set_theme_style()
        self.setup_ui()

        self.pw_input.textChanged.connect(self.dis_encrypt)

    def fill(self, data):
        self.username_input.setText(data['username'])
        self.pw_input.setText(data['password'])
        self.is_encrypted = True

    def set_theme_style(self):
        pass

    def setup_ui(self):
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
        self._app.pixmap_from_url(url, self.captcha_label.setPixmap)

    def dis_encrypt(self, text):
        self.is_encrypted = False


class LoginButton(QLabel):
    clicked = pyqtSignal()

    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setText('登录')
        self.setToolTip('登陆网易云音乐')
        self.setObjectName('nem_login_btn')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color4.name())
        self.setStyleSheet(style_str)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()

    def set_avatar(self, url):
        pixmap = self._app.pixmap_from_url(url)
        if pixmap is not None:
            self.setPixmap(pixmap.scaled(self.size(),
                           transformMode=Qt.SmoothTransformation))


class _TagCellWidget(QFrame):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self.setObjectName('tag_cell')

        self.download_tag = QLabel('✓', self)
        self.download_flag = False
        self.download_tag.setObjectName('download_tag')
        self.download_tag.setAlignment(Qt.AlignCenter)

        self.set_theme_style()

        self._layout = QHBoxLayout(self)
        self.setup_ui()

    @property
    def download_label_style(self):
        theme = self._app.theme_manager.current_theme
        background = set_alpha(theme.color7, 50).name(QColor.HexArgb)
        if self.download_flag:
            color = theme.color4.name()
        else:
            color = set_alpha(theme.color7, 30).name(QColor.HexArgb)
        style_str = '''
            #download_tag {{
                color: {0};
                background: {1};
                border-radius: 10px;
            }}
        '''.format(color, background)
        return style_str

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        style_str = style_str + self.download_label_style

        self.setStyleSheet(style_str)

    def set_download_tag(self):
        self.download_flag = True
        self.set_theme_style()

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(10)
        self._layout.addWidget(self.download_tag)
        self._layout.addSpacing(10)
        self._layout.addStretch(1)
        self.download_tag.setFixedSize(20, 20)



class Ui(object):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.login_dialog = LoginDialog(self._app, self._app)
        self.login_btn = LoginButton(self._app)
        self._lb_container = QFrame()

        self._lbc_layout = QHBoxLayout(self._lb_container)

        self.setup()

    def setup(self):

        self._lbc_layout.setContentsMargins(0, 0, 0, 0)
        self._lbc_layout.setSpacing(0)

        self._lbc_layout.addWidget(self.login_btn)
        self.login_btn.setFixedSize(30, 30)
        self._lbc_layout.addSpacing(10)

        tp_layout = self._app.ui.top_panel.layout()
        tp_layout.addWidget(self._lb_container)

    def on_login_in(self):
        self.login_btn.setToolTip('点击可刷新歌单列表')
        if self.login_dialog.isVisible():
            self.login_dialog.hide()
