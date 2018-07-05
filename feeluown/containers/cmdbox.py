import io
import sys

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QLineEdit


class CmdBox(QLineEdit):
    # FIXME: please rename CmdBox to ___

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app

        self.setPlaceholderText('搜索歌曲、歌手、专辑、用户')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setTextMargins(5, 0, 0, 0)

        self._timer = QTimer(self)
        self._cmd_text = None
        self._text_type = 'cmd'  # ['msg', 'cmd']
        self._timer.timeout.connect(self.__on_timeout)

        self.textEdited.connect(self.__on_text_edited)
        self.returnPressed.connect(self.__on_return_pressed)

    def show_msg(self, text, timeout=1000):
        if not text:
            return
        if self._text_type == 'cmd':
            self.setReadOnly(True)
            self._text_type = 'msg'
            self._cmd_text = self.text()
        assert self.isReadOnly() is True
        self.setText(text)
        if timeout > 0:
            self._timer.start(timeout)

    def _restore_cmd_text(self):
        self.setReadOnly(False)
        self._text_type = 'cmd'
        self.setText(self._cmd_text)

    def _search_library(self, q):
        songs = self._app.provider_manager.search(q)
        self._app.ui.table_container.show_songs(songs)

    def _exec_code(self, code):
        output = io.StringIO()
        sys.stderr = output
        sys.stdout = output
        try:
            self._app.exec_(code)
        except Exception as e:
            print(str(e))
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
        self.show_msg(output.getvalue())

    def __on_text_edited(self, text):
        if self._text_type == 'cmd':
            self._cmd_text = text
        if not text.startswith('>'):
            self._app.ui.table_container.search(text)

    def __on_return_pressed(self):
        text = self.text()
        if text.startswith('>>> '):
            self._exec_code(text[4:])
        else:
            self._search_library(text)

    def __on_timeout(self):
        self._timer.stop()
        self._restore_cmd_text()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._timer.stop()
        self._restore_cmd_text()
