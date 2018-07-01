from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QLineEdit


class CmdBox(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setPlaceholderText('搜索歌曲、歌手、专辑、用户')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setTextMargins(5, 0, 0, 0)

        self._timer = QTimer(self)
        self._cmd_text = None
        self._text_type = 'cmd'  # ['msg', 'cmd']
        self._timer.timeout.connect(self._on_timeout)

        self.textEdited.connect(self.on_text_edited)

    def on_text_edited(self, text):
        if self._text_type == 'cmd':
            self._cmd_text = text

    def show_msg(self, text, timeout=1000):
        if self._text_type == 'cmd':
            self.setReadOnly(True)
            self._text_type = 'msg'
            self._cmd_text = self.text()
        assert self.isReadOnly() is True
        self.setText(text)
        if timeout > 0:
            self._timer.start(timeout)

    def restore_cmd_text(self):
        self.setReadOnly(False)
        self._text_type = 'cmd'
        self.setText(self._cmd_text)

    def _on_timeout(self):
        self.restore_cmd_text()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._timer.stop()
        self.restore_cmd_text()
