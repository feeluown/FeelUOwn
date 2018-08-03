import io
import sys

from PyQt5.QtCore import (
    pyqtSignal,
    QSize,
    Qt,
    QRect,
    QTimer,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QTextCursor,
    QFontDatabase,
    QFontMetrics,
    QPainter,
    QPalette,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QStyle,
    QStyleOptionFrame,
    QTextEdit,
)


class Highlighter(QSyntaxHighlighter):
    """
    Python REPL 和 fuo 命令语法高亮
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        prompt_fmt = QTextCharFormat()
        prompt_fmt.setFontWeight(QFont.Bold)
        self._prompt_fmt = prompt_fmt

    def highlightBlock(self, text):
        if text.startswith('>>> '):
            self.setFormat(0, 3, self._prompt_fmt)


class MagicBox(QTextEdit):
    """读取用户输入，解析执行

    ref: https://wiki.qt.io/Technical_FAQ #How can I create a one-line QTextEdit?
    """

    returnPressed = pyqtSignal()

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        # self.setPlaceholderText('搜索歌曲、歌手、专辑、用户；执行 Python 代码等')
        self.setPlaceholderText('Search library, exec code, or run command.')
        self.setToolTip('直接输入文字可以进行过滤，按 Enter 可以搜索\n'
                        '输入 >>> 前缀之后，可以执行 Python 代码\n'
                        '输入 $ 前缀可以执行 fuo 命令（未实现，欢迎 PR）')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

        # 模拟 QLineEdit
        self.setTabChangesFocus(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumHeight(25)

        self._timer = QTimer(self)
        self._cmd_text = None
        self._mode = 'cmd'  # 详见 _set_mode 函数
        self._timer.timeout.connect(self.__on_timeout)

        self.textChanged.connect(self.__on_text_edited)
        self._highlighter = Highlighter(self.document())
        # self.textEdited.connect(self.__on_text_edited)
        self.returnPressed.connect(self.__on_return_pressed)

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
            if self._cmd_text:
                self.setHtml(self._cmd_text)
            # 注意在所有操作完成之后再关闭 blockSignals
            # 然后修改当前 mode
            self.blockSignals(False)
            self._mode = mode
        elif mode == 'msg':
            self.blockSignals(True)
            if self._mode == 'cmd':
                self.setReadOnly(True)
                self._cmd_text = self.toHtml()
                self._mode = mode

    def _search_library(self, q):
        songs = []
        for result in self._app.library.search(q):
            songs.extend(result.songs)
        self._app.ui.table_container.show_songs(songs)

    def _exec_code(self, code):
        """执行代码并重定向代码的 stdout/stderr"""
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
        self.show_msg(output.getvalue() or 'No output.')

    def __on_text_edited(self):
        text = self.toPlainText()
        if self._mode == 'cmd':
            self._cmd_text = self.toHtml()
        if not text.startswith('>'):
            self._app.ui.table_container.search(text)

    def __on_return_pressed(self):
        text = self.toPlainText()
        if text.startswith('>>> '):
            self._exec_code(text[4:])
        else:
            self._search_library(text)

    def __on_timeout(self):
        self._set_mode('cmd')

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._set_mode('cmd')

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.returnPressed.emit()
            e.ignore()
        else:
            super().keyPressEvent(e)

    def wheelEvent(self, e):
        if self._mode != 'cmd':
            super().wheelEvent(e)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        # FIXME: 暂时不是太懂应该怎样正确的计算 w 和 h
        # 计算 h 的一个原则是让高度正好能够显示一行
        h = max(fm.height() + fm.ascent() - fm.descent(), 14)
        w = self.width() - 4
        opt = QStyleOptionFrame()
        opt.initFrom(self)
        return self.style().sizeFromContents(
            QStyle.CT_LineEdit,
            opt,
            QSize(w, h).expandedTo(QApplication.globalStrut()),
            self
        )
