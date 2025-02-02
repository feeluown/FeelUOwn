import io
import sys
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QSizePolicy

from feeluown.library.text2song import create_dummy_brief_song
from feeluown.fuoexec import fuoexec
from feeluown.utils.aio import run_afn

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

_KeyPrefix = 'search_'  # local storage key prefix
KeySourceIn = _KeyPrefix + 'source_in'
KeyType = _KeyPrefix + 'type'


class MagicBox(QLineEdit):
    """读取用户输入，解析执行

    ref: https://wiki.qt.io/Technical_FAQ #How can I create a one-line QTextEdit?
    """

    # this filter signal is designed for table (songs_table & albums_table)
    filter_text_changed = pyqtSignal(str)

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent)

        self._app = app
        self.setPlaceholderText('搜索歌曲、歌手、专辑、用户')
        self.setToolTip(
            '直接输入文字可以进行过滤，按 Enter 可以搜索\n'
            '输入 >>> 前缀之后，可以执行 Python 代码\n'
            '输入 “==> 执迷不悔 | 王菲”，可以直接播放歌曲\n'
            '输入 “=== 下雨天听点啥？”，可以和 AI 互动\n'
            '输入 # 前缀之后，可以过滤表格内容\n'
            '输入 > 前缀可以执行 fuo 命令（未实现，欢迎 PR）'
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(32)
        self.setFrame(False)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setTextMargins(5, 0, 0, 0)

        self._timer = QTimer(self)
        self._cmd_text = None
        self._mode = 'cmd'  # 详见 _set_mode 函数
        self._timer.timeout.connect(self.__on_timeout)

        self.textChanged.connect(self.__on_text_edited)
        # self.textEdited.connect(self.__on_text_edited)
        self.returnPressed.connect(self.__on_return_pressed)

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

        text = output.getvalue()
        self._set_mode('msg')
        self.setText(text or 'No output.')
        self._timer.start(1000)
        if text:
            self._app.show_msg(text)

    def __on_text_edited(self):
        text = self.text()
        if self._mode == 'cmd':
            self._cmd_text = text
        # filter browser content if prefix starts with `#`
        # TODO: cancel unneeded filter
        if text.startswith('#'):
            self.filter_text_changed.emit(text[1:].strip())
        else:
            self.filter_text_changed.emit('')

    def __on_return_pressed(self):
        text = self.text()
        if text.startswith('>>> '):
            self._exec_code(text[4:])
        elif text.startswith('---') or text.startswith('==='):
            if self._app.ui.ai_chat_overlay is not None:
                body = text[4:] if len(text) > 4 else ''
                if body:
                    run_afn(self._app.ui.ai_chat_overlay.body.exec_user_query, body)
                self._app.ui.ai_chat_overlay.show()
            else:
                self._app.show_msg('AI 聊天功能不可用')
        elif text.startswith('--> ') or text.startswith('==> ') \
                or text.startswith('--》') or text.startswith('==》'):
            body = text[4:]
            if not body:
                return
            delimiters = ('|', '-')
            title = artists_name = ''
            for delimiter in delimiters:
                parts = body.split(delimiter)
                if len(parts) == 2:
                    title, artists_name = parts
                    break
            if title and artists_name:
                song = create_dummy_brief_song(title.strip(), artists_name.strip())
                self._app.playlist.play_model(song)
                self._app.show_msg(f'尝试播放：{song}')
            else:
                self._app.show_msg('你输入的内容需要符合格式：“歌曲标题 | 歌手名”')
        else:
            local_storage = self._app.browser.local_storage
            type_ = local_storage.get(KeyType)
            source_in = local_storage.get(KeySourceIn)
            query = {'q': text}
            if type_ is not None:
                query['type'] = type_
            if source_in is not None:
                query['source_in'] = source_in
            self._app.browser.goto(page='/search', query=query)

    def __on_timeout(self):
        self._set_mode('cmd')

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._set_mode('cmd')
