import json
import uuid
from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtGui import QResizeEvent, QColor, QFontDatabase
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QPlainTextEdit,
    QLabel,
)

from feeluown.library import BriefSongModel, ModelState

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Text2SongsOverlay(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._editor = QPlainTextEdit(self)
        self._msg_label = QLabel(self)
        self._test_btn = QPushButton('尝试解析一下', self)
        self._submit_btn = QPushButton('添加到播放列表', self)
        self._hide_btn = QPushButton('关闭窗口', self)

        # self.setFocusPolicy(Qt.ClickFocus)
        self.setup_ui()

        self._test_btn.clicked.connect(self.parse_editor_text)
        self._submit_btn.clicked.connect(self._on_submit)
        self._hide_btn.clicked.connect(self.hide)

    def setup_ui(self):
        self._app.installEventFilter(self)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPixelSize(13)
        self._editor.setFont(font)
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._msg_label.setTextFormat(Qt.RichText)

        self._layout = QHBoxLayout(self)
        self._v_layout = QVBoxLayout()
        self._btn_layout = QVBoxLayout()
        self._layout.addStretch(0)
        self._layout.addLayout(self._v_layout)
        self._layout.setStretch(1, 1)
        self._layout.addSpacing(20)
        self._layout.addLayout(self._btn_layout)
        self._layout.addStretch(0)
        self._layout.setContentsMargins(100, 80, 100, 80)

        self._v_layout.addWidget(self._editor)
        self._v_layout.addWidget(self._msg_label)
        self._btn_layout.addWidget(self._test_btn)
        self._btn_layout.addWidget(self._submit_btn)
        self._btn_layout.addWidget(self._hide_btn)
        self._btn_layout.addStretch(0)

    def parse_editor_text(self):
        text = self._editor.toPlainText()

        def json_fn(each):
            try:
                return each['title'], each['artists_name']
            except KeyError:
                return None

        def line_fn(line):
            parts = line.split('|')
            if len(parts) == 2 and parts[0]:  # title should not be empty
                return (parts[0], parts[1])
            return None

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            lines = text.split('\n')
            if not (lines and lines[0].strip() in ('---', '===')):
                self.set_msg('你需要填入一个合法的 JSON', level='err')
                return
            parse_each_fn = line_fn
            items = [each.strip() for each in lines[1:] if each.strip()]
        else:
            if not isinstance(data, list):
                self.set_msg(
                    '你需要填入一个歌曲列表，格式类似 [{"title": "xxx", "artists_name": "yyy"}]',
                    level='err'
                )
                return
            parse_each_fn = json_fn
            items = data

        err_count = 0
        songs = []
        for each in items:
            result = parse_each_fn(each)
            if result is not None:
                title, artists_name = result
                song = BriefSongModel(
                    source='dummy',
                    identifier=str(uuid.uuid4()),
                    title=title,
                    artists_name=artists_name,
                    state=ModelState.not_exists,
                )
                songs.append(song)
            else:
                err_count += 1

        if err_count > 0:
            if songs:
                level = 'warn'
            else:
                level = 'err'
        else:
            level = 'hint'
        self.set_msg(f'解析成功的歌曲数：{len(songs)}，失败：{err_count}', level=level)
        return songs

    def set_msg(self, text, level='hint'):
        if level == 'hint':
            color = 'green'
        elif level == 'warn':
            color = 'yellow'
        else:  # err
            color = 'red'
        self._msg_label.setText(f'<span style="color: {color}">{text}</span>')

    def _on_submit(self):
        songs = self.parse_editor_text()
        for song in songs:
            self._app.playlist.add(song)
        self._app.show_msg(f'添加{len(songs)}首歌曲到播放列表')
        self.hide()

    def paintEvent(self, a0):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def showEvent(self, e):
        self.resize(self._app.size())
        super().showEvent(e)
        self.raise_()

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False

    def focusInEvent(self, event):
        self.hide()
        super().focusInEvent(event)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QWidget

    from feeluown.gui.debug import simple_layout, mock_app

    with simple_layout(theme='dark') as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        widget = Text2SongsOverlay(app)
        widget.resize(600, 400)
        layout.addWidget(widget)
