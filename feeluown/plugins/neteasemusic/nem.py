import json
import os

from PyQt5.QtCore import QObject

from .consts import USER_PW_FILE
from .ui import Ui


class Nem(QObject):
    instance = None

    def __init__(self, app):
        if Nem.instance is not None:
            return Nem.instance

        super().__init__(parent=app)
        self._app = app

        self.ui = Ui(self._app)

        self.init_signal_binding()

    def init_signal_binding(self):
        self.ui.login_btn.clicked.connect(self.show_login_dialog)
        self.ui.login_dialog.ok_btn.clicked.connect(self.login)

    def load_user_pw(self):
        if not os.path.exists(USER_PW_FILE):
            return
        with open(USER_PW_FILE, 'r') as f:
            d = json.load(f)
            data = d[d['default']]
        return data

    def save_user_pw(self, data):
        with open(USER_PW_FILE, 'w+') as f:
            if f.read() == '':
                d = dict()
            else:
                d = json.load(f)
            d['default'] = data['username']
            d['username'] = data
            json.dump(d, f, indent=4)

    def show_login_dialog(self):
        self.ui.login_dialog.show()

    def login(self):
        login_dialog = self.ui.login_dialog
        print(login_dialog.data)
