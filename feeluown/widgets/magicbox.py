import io
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFontDatabase, QKeySequence
from PyQt5.QtWidgets import QLineEdit, QSizePolicy

from feeluown.fuoexec import fuoexec


class MagicBox(QLineEdit):
    """读取用户输入，解析执行

    ref: https://wiki.qt.io/Technical_FAQ #How can I create a one-line QTextEdit?
    """

    # this filter signal is designed for table (songs_table & albums_table)
    filter_text_changed = pyqtSignal(str)

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self.setPlaceholderText('搜索歌曲、歌手、专辑、用户')
        self.setToolTip('直接输入文字可以进行过滤，按 Enter 可以搜索\n'
                        '输入 >>> 前缀之后，可以执行 Python 代码\n'
                        '输入 > 前缀可以执行 fuo 命令（未实现，欢迎 PR）')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(32)
        self.setFrame(False)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setTextMargins(5, 0, 0, 0)

        self._timer = QTimer(self)
        self._cmd_text = None
        self._mode = 'cmd'  # 详见 _set_mode 函数
        self._timer.timeout.connect(self.__on_timeout)

        self.textChanged.connect(self.__on_text_edited)
        # self.textEdited.connect(self.__on_text_edited)
        self.returnPressed.connect(self.__on_return_pressed)
        self._app.browser.route('/search')(self.__handle_search)

        self._app.hotkey_mgr.register(
            [QKeySequence('Ctrl+F'), QKeySequence(':'), QKeySequence('Alt+x')],
            self.setFocus
        )

    def show_msg(self, text, timeout=2000):
        if not text:
            return
        self._set_mode('msg')
        self.setText(text)
        if timeout > 0:
            self._timer.start(timeout)

    def _set_mode(self, mode):
        """修改当前模式

        现在主要有两种模式：cmd 模式是正常模式；msg 模式用来展示消息通知，
        当自己处于 msg 模式下时，会 block 所有 signal
        """
        if mode == 'cmd':
            self.setReadOnly(False)
            self._timer.stop()
            self.setText(self._cmd_text or '')
            # 注意在所有操作完成之后再关闭 blockSignals
            # 然后修改当前 mode
            self.blockSignals(False)
            self._mode = mode
        elif mode == 'msg':
            self.blockSignals(True)
            if self._mode == 'cmd':
                self.setReadOnly(True)
                self._cmd_text = self.text()
                self._mode = mode

    def __handle_search(self, req):
        q = req.query.get('q', '')
        if q:
            self._search_library(q)

    def _search_library(self, q):
        songs = []
        for result in self._app.library.search(q):
            songs.extend(result.songs or [])
        self._app.ui.right_panel.show_songs(songs)

    def _exec_code(self, code):
        """执行代码并重定向代码的 stdout/stderr"""
        output = io.StringIO()
        sys.stderr = output
        sys.stdout = output
        try:
            obj = compile(code, '<string>', 'single')
            fuoexec(obj)
        except Exception as e:
            print(str(e))
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
        self.show_msg(output.getvalue() or 'No output.')

    def __on_text_edited(self):
        text = self.text()
        if self._mode == 'cmd':
            self._cmd_text = text
        if not text.startswith('>'):
            self.filter_text_changed.emit(text)

    def __on_return_pressed(self):
        text = self.text()
        if text.startswith('>>> '):
            self._exec_code(text[4:])
        else:
            self._app.browser.goto(uri='/search', query={'q': text})

    def __on_timeout(self):
        self._set_mode('cmd')

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._set_mode('cmd')
