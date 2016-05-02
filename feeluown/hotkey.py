from PyQt5.QtWidgets import QShortcut


class Hotkey(object):
    def __init__(self, app):
        self._app = app

    def registe(self, key_sequence, callback):
        shortcut = QShortcut(key_sequence, self._app)
        shortcut.activated.connect(callback)
