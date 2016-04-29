import json
import logging
import os

from PyQt5.QtCore import QObject

from .consts import USER_PW_FILE
from .model import NUserModel, NSongModel
from .ui import Ui, SongsTable, SongsTable_Container

logger = logging.getLogger(__name__)


class Nem(QObject):
    instance = None

    def __init__(self, app):
        if Nem.instance is not None:
            return Nem.instance

        super().__init__(parent=app)
        self._app = app

        self.ui = Ui(self._app)

        self.user = None

        self.init_signal_binding()
        self.test()

    def init_signal_binding(self):
        self.ui.login_btn.clicked.connect(self.ready_to_login)
        self.ui.login_dialog.ok_btn.clicked.connect(self.login)

    def load_user_pw(self):
        if not os.path.exists(USER_PW_FILE):
            return
        with open(USER_PW_FILE, 'r') as f:
            d = json.load(f)
            data = d[d['default']]
        self.ui.login_dialog.username_input.setText(data['username'])
        self.ui.login_dialog.pw_input.setText(data['password'])
        self.ui.login_dialog.is_encrypted = True

        logger.info('load username and password from %s' % USER_PW_FILE)

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

    def ready_to_login(self):
        model = NUserModel.load()
        if model is None:
            self.ui.login_dialog.show()
            self.load_user_pw()
        else:
            logger.info('load last user.')
            self.user = model
            self._on_login_in()

    def login(self):
        login_dialog = self.ui.login_dialog
        if login_dialog.captcha_needed:
            captcha = str(login_dialog.captcha_input.text())
            captcha_id = login_dialog.captcha_id
            data = NUserModel.check_captcha(captcha_id, captcha)
            if data['code'] == 200:
                login_dialog.captcha_input.hide()
                login_dialog.captcha_label.hide()
            else:
                login_dialog.captcha_verify(data)

        user_data = login_dialog.data
        self.ui.login_dialog.show_hint('正在登录...')
        data = NUserModel.check(user_data['username'], user_data['password'])
        message = data['message']
        self.ui.login_dialog.show_hint(message)
        if data['code'] == 200:
            # login in
            self.save_user_pw(user_data)
            self.user = NUserModel.create(data)
            self._on_login_in()
        elif data['code'] == 415:
            login_dialog.captcha_verify(data)

    def _on_login_in(self):
        logger.info('login in... set user infos.')
        self.ui.login_dialog.close()
        self.ui.login_btn.set_avatar(self.user.img)
        self.user.save()
        self.load_playlists()

    def load_playlists(self):
        print('load user playlists')

    def test(self):
        self.songs_table = SongsTable(self._app)
        self.songs_table_container = SongsTable_Container(self._app)
        self.songs_table_container.set_table(self.songs_table)
        right_panel = self._app.ui.central_panel.right_panel
        right_panel.layout().addWidget(self.songs_table_container)
        model = NSongModel.get(210049)
        for i in range(0, 20):
            self.songs_table.add_item(model)
