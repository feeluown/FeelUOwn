import asyncio
import json
import uuid
import socket
import logging
from typing import TYPE_CHECKING, cast, List
from dataclasses import dataclass

from openai import AsyncOpenAI
from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtGui import QResizeEvent, QColor, QFontDatabase, QPainter
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QFrame,
    QPlainTextEdit,
    QLabel,
    QScrollArea,
)

from feeluown.utils.aio import run_afn_ref, run_afn
from feeluown.library import BriefSongModel, ModelState
from feeluown.library.text2song import analyze_text, create_dummy_brief_song
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.utils.utils import elfhash


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


QUERY_PROMPT = '''你是一个音乐播放器助手。'''
EXTRACT_PROMPT = '''\
提取上面的歌曲信息，并补全每首歌的歌曲名和歌手名。每首歌一行 JSON，用类似下面这样的格式返回
    {"title": "xxx", "artists_name": "yyy", "description": "推荐理由1"}
    {"title": "aaa", "artists_name": "bbb", "description": "推荐理由2"}

注意，你返回的内容只应该有几行 JSON，其它信息都不需要。也不要用 markdown 格式返回。
'''


@dataclass
class ChatContext:
    client: AsyncOpenAI
    messages: List


class AIChatOverlay(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.body = Body(app, self)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(100, 80, 100, 80)
        self._layout.addWidget(self.body)

    def paintEvent(self, a0):
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


class Body(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._scrollarea = QScrollArea(self)
        self._label = QLabel()
        self._scrollarea.setWidget(self._label)
        self._msg_label = QLabel(self)
        self._hide_btn = TextButton('关闭窗口', self)
        self._extract_and_play_btn = TextButton('提取歌曲并播放', self)
        self._extract_10_and_play_btn = TextButton('提取10首并播放', self)

        self.setup_ui()
        self._hide_btn.clicked.connect(self._hide)
        self._extract_and_play_btn.clicked.connect(lambda: run_afn_ref(self.extract_and_play))
        self._extract_10_and_play_btn.clicked.connect(lambda: run_afn_ref(self.extract_10_and_play))

        self._chat_context = None
        self.setAutoFillBackground(True)

    def setup_ui(self):
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._msg_label.setWordWrap(True)
        self._scrollarea.setWidgetResizable(True)
        self._app.installEventFilter(self)
        self._msg_label.setTextFormat(Qt.RichText)

        self._layout = QHBoxLayout(self)
        self._v_layout = QVBoxLayout()
        self._btn_layout = QVBoxLayout()
        self._layout.addStretch(0)
        self._layout.addLayout(self._v_layout)
        self._layout.setStretch(1, 1)
        self._layout.addLayout(self._btn_layout)
        self._layout.addStretch(0)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)

        self._v_layout.addWidget(self._scrollarea)
        self._v_layout.addWidget(self._msg_label)
        self._btn_layout.addWidget(self._extract_and_play_btn)
        self._btn_layout.addWidget(self._extract_10_and_play_btn)
        self._btn_layout.addWidget(self._hide_btn)
        self._btn_layout.addStretch(0)

    async def exec_user_query(self, query):
        self.set_msg('等待 AI 返回中...', level='hint')
        client = AsyncOpenAI(
            base_url=self._app.config.OPENAI_API_BASEURL,
            api_key=self._app.config.OPENAI_API_KEY,
        )
        messages = [
            {'role': 'system', 'content': QUERY_PROMPT},
            {'role': 'user', 'content': query}
        ]
        self._chat_context = ChatContext(client, messages)
        stream = await client.chat.completions.create(
            model=self._app.config.OPENAI_MODEL,
            messages=messages,
            stream=True,
        )
        content = ''
        async for chunk in stream:
            self.set_msg('AI 返回中...', level='hint')
            content += chunk.choices[0].delta.content or ''
            self.show_chat_message(content)
        assistant_message = {"role": "assistant", "content": content}
        self._chat_context.messages.append(assistant_message)
        self.set_msg('AI 内容返回结束', level='hint')

    def show_chat_message(self, text):
        self._label.setText(text)

    def set_msg(self, text, level='hint'):
        if level == 'hint':
            color = 'green'
        elif level == 'warn':
            color = 'yellow'
        else:  # err
            color = 'red'
        self._msg_label.setText(f'<span style="color: {color}">{text}</span>')

    async def extract_and_play(self):
        await self._extract_and_play(EXTRACT_PROMPT)

    async def extract_10_and_play(self):
        await self._extract_and_play(f'{EXTRACT_PROMPT}\n随机提取最多10首即可')

    async def _extract_and_play(self, extract_prompt):
        message = {'role': 'user', 'content': extract_prompt}
        self._chat_context.messages.append(message)
        self.set_msg('正在让 AI 解析歌曲信息，这可能会花费一些时间...')
        stream = await self._chat_context.client.chat.completions.create(
            model=self._app.config.OPENAI_MODEL,
            messages=self._chat_context.messages,
            stream=True,
        )
        rsock, wsock = socket.socketpair()
        reader1, writer1 = await asyncio.open_connection(sock=rsock)
        _, writer2 = await asyncio.open_connection(sock=wsock)

        async def write_task():
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ''
                writer2.write(content.encode('utf-8'))
            writer2.write_eof()
            await writer2.drain()
            writer2.close()
            await writer2.wait_closed()

        task = run_afn(write_task)
        ok_count = 0
        fail_count = 0
        while True:
            try:
                line = await reader1.readline()
                line = line.decode('utf-8')
                logger.debug(f'read a line: {line}')
                if not line:
                    self.set_msg(f'解析结束，成功解析{ok_count}首歌曲，失败{fail_count}首歌。',
                                 level='hint')
                    break
                try:
                    jline = json.loads(line)
                    title, artists_name = jline['title'], jline['artists_name']
                except:
                    fail_count += 1
                    logger.exception(f'failed to parse a line: {line}')
                    self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                 level='yellow')
                else:
                    song = create_dummy_brief_song(title, artists_name)
                    ok_count += 1
                    self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                 level='hint')
                    self._app.playlist.add(song)
                    if ok_count == 1:
                        self._app.playlist.play_model(song)
            except:
                logger.exception('extract and play failed')
                break

        await task
        writer1.close()
        await writer1.wait_closed()
        self._hide()

    def _hide(self):
        self.parent().hide()


if __name__ == '__main__':
    import os
    from PyQt5.QtWidgets import QWidget
    from feeluown.gui.debug import simple_layout, mock_app

    with simple_layout(theme='dark') as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        app.config.OPENAI_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
        app.config.OPENAI_API_BASEURL = 'https://api.deepseek.com'
        app.config.OPENAI_MODEL = 'deepseek-chat'
        widget = AIChatOverlay(app)
        widget.resize(600, 400)
        layout.addWidget(widget)
        widget.show()
        widget.body.show_chat_message('Hello, feeluown!' * 100)
