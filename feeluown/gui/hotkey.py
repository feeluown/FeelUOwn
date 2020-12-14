from PyQt5.QtWidgets import QShortcut


class HotkeyManager(object):
    """集中管理各个组件的快捷键"""

    def __init__(self, app):
        self._app = app

    def register(self, key_sequences, callback):
        if isinstance(key_sequences, list):
            key_sequences = key_sequences
        else:
            key_sequences = [key_sequences]

        for key_sequence in key_sequences:
            shortcut = QShortcut(key_sequence, self._app)
            shortcut.activated.connect(callback)
