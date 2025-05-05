import json
import logging
from typing import TYPE_CHECKING, List

from openai import AsyncOpenAI
from PyQt5.QtCore import QSize, Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QLabel, QScrollArea, QPlainTextEdit,
    QFrame, QSizePolicy,
)
from PyQt5.QtGui import QPainterPath
from PyQt5.QtGui import QTextOption

from feeluown.ai import a_handle_stream
from feeluown.utils.aio import run_afn_ref
from feeluown.library import fmt_artists_names
from feeluown.library.text2song import create_dummy_brief_song
from feeluown.gui.helpers import palette_set_bg_color
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.header import MidHeader
from feeluown.gui.components.overlay import AppOverlayContainer


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


QUERY_PROMPT = '''你是一个音乐播放器助手。'''
EXTRACT_PROMPT = '''\
提取歌曲信息，歌手名为空的话，你需要补全，每首歌一行 JSON，用类似下面这样的格式返回
    {"title": "t1", "artists": ["a1", "a11"], "description": "推荐理由1"}
    {"title": "t2", "artists": ["a11"], "description": "推荐理由2"}

注意，你返回的内容只应该有几行 JSON，其它信息都不需要。也不要用 markdown 格式返回。
'''


class ChatContext:
    def __init__(self, model: str, client: AsyncOpenAI, messages: List):
        self.model = model
        self.client = client
        self.messages = messages

    async def send_message(self):
        return await self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
            stream_options={'include_usage': True},
        )


class ChatInputEditor(QPlainTextEdit):
    """Custom editor for chat input with Enter key handling"""

    enter_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.setMinimumHeight(30)
        self.setMaximumHeight(300)  # TODO: set maximum height based on parent size
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()
        # The size policy matters
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def sizeHint(self) -> QSize:  # noqa: D102
        font_metrics = self.fontMetrics()
        line_height = font_metrics.lineSpacing()
        doc = self.document()
        line_count = doc.lineCount()
        doc_height = line_count * line_height

        # Add some padding, 10
        new_height = min(max(int(doc_height) + 10, self.minimumHeight()),
                         self.maximumHeight())
        return QSize(super().sizeHint().width(), new_height)

    def adjust_height(self):
        self.updateGeometry()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers():
            self.enter_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class RoundedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._radius = 8
        self._padding = 8
        self.setContentsMargins(self._padding, self._padding,
                                self._padding, self._padding)
        self.setWordWrap(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        # Fill background
        painter.fillPath(path, self.palette().color(self.backgroundRole()))
        super().paintEvent(event)


class Body(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        # Chat history display area
        self._history_area = QScrollArea(self)
        self._history_widget = QWidget()
        self._history_area.setWidget(self._history_widget)
        self._history_layout = QVBoxLayout(self._history_widget)

        # User input area
        self._editor = ChatInputEditor(self)
        self._editor.setPlaceholderText('在这里输入你的问题...')
        self._editor.setFrameShape(QFrame.NoFrame)
        self._editor.enter_pressed.connect(
            lambda: run_afn_ref(self.exec_user_query, self._editor.toPlainText()))
        self._msg_label = QLabel(self)
        self._msg_label.setWordWrap(True)
        self._hide_btn = TextButton('关闭窗口', self)
        self._extract_and_play_btn = TextButton('提取歌曲并播放', self)
        self._extract_10_and_play_btn = TextButton('提取10首并播放', self)
        self._send_btn = TextButton('发送（回车）', self)
        self._clear_history_btn = TextButton('清空对话', self)

        self.setup_ui()
        self._hide_btn.clicked.connect(self.hide)
        self._extract_and_play_btn.clicked.connect(
            lambda: run_afn_ref(self.extract_and_play))
        self._extract_10_and_play_btn.clicked.connect(
            lambda: run_afn_ref(self.extract_10_and_play))
        self._send_btn.clicked.connect(
            lambda: run_afn_ref(self.exec_user_query, self._editor.toPlainText()))
        self._clear_history_btn.clicked.connect(self.clear_history)

        self._chat_context = None
        self.setAutoFillBackground(True)

    def setup_ui(self):
        self._history_area.setFrameShape(QFrame.NoFrame)
        self._history_area.setAutoFillBackground(True)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(5)
        self._history_area.setWidgetResizable(True)
        # Adjust spacing between messages
        self._history_layout.setSpacing(10)

        self._msg_label.setWordWrap(True)
        self._app.installEventFilter(self)
        self._msg_label.setTextFormat(Qt.RichText)

        self._root_layout = QVBoxLayout(self)
        self._layout = QHBoxLayout()
        self._v_layout = QVBoxLayout()
        self._btn_layout = QVBoxLayout()

        self._root_layout.addWidget(MidHeader('AI 助手'))
        self._root_layout.addLayout(self._layout)
        self._layout.addStretch(0)
        self._layout.addLayout(self._v_layout)
        self._layout.setStretch(1, 1)
        self._layout.addLayout(self._btn_layout)
        self._layout.addStretch(0)
        self._root_layout.setContentsMargins(10, 10, 10, 10)
        self._root_layout.setSpacing(10)

        # Adjust layout to add chat history area
        self._v_layout.addWidget(self._history_area)
        self._v_layout.addWidget(self._msg_label)
        self._v_layout.addWidget(self._editor)
        self._btn_layout.addWidget(self._extract_and_play_btn)
        self._btn_layout.addWidget(self._extract_10_and_play_btn)
        self._btn_layout.addWidget(self._clear_history_btn)
        self._btn_layout.addWidget(self._hide_btn)
        self._btn_layout.addStretch(0)
        self._btn_layout.addWidget(self._send_btn)

    def _create_message_label(self, role, content):
        """Create message label"""
        label = RoundedLabel()
        label.setText(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setFrameStyle(QFrame.NoFrame)

        width_factor = 0.6 if role in ('user', 'system') else 1
        label.setMaximumWidth(int(self._history_area.width() * width_factor))
        label.setAlignment(Qt.AlignLeft)

        pal = label.palette()
        if role in ('user', 'system'):
            origin_window = pal.color(pal.Window)
            palette_set_bg_color(pal, pal.color(pal.Highlight))
            pal.setColor(pal.Text, pal.color(pal.HighlightedText))
            pal.setColor(pal.Highlight, origin_window)
            label.setPalette(pal)

        return label

    def _add_message_to_history(self, role, content):
        """Add message to chat history"""
        self._chat_context.messages.append({'role': role, 'content': content})
        label = self._create_message_label(role, content)
        self._history_layout.addWidget(label)
        self._scroll_to_bottom()

    async def exec_user_query(self, query):
        if self._chat_context is None:
            self._chat_context = self.create_chat_context()

        self._add_message_to_history('user', query)
        self.set_msg('等待 AI 返回中...', level='hint')
        try:
            stream = await self._chat_context.send_message()
        except Exception as e:  # noqa
            self.set_msg(f'调用 AI 接口失败: {e}', level='err')
            logger.exception('AI request failed')
        else:
            # Create label for AI response
            ai_label = self._create_message_label('assistant', '')
            self._history_layout.addWidget(ai_label)

            content = ''
            async for chunk in stream:
                self.set_msg('AI 返回中...', level='hint')
                # 当使用 stream_options 时，最后一个 chunk 的 choices 为空
                if chunk.choices:
                    delta_content = chunk.choices[0].delta.content or ''
                    content += delta_content
                    # Update AI response in real-time
                    ai_label.setText(content)
                    self._scroll_to_bottom()

            # Update chat context and show token usage
            assistant_message = {"role": "assistant", "content": content}
            self._chat_context.messages.append(assistant_message)
            self.show_tokens_usage(chunk)
            # Clear input box
            self._editor.clear()

    def show_tokens_usage(self, chunk):
        if not chunk:
            self.set_msg('AI 内容返回结束', level='hint')
            return

        in_tokens = chunk.usage.prompt_tokens if chunk.usage else 0
        out_tokens = chunk.usage.completion_tokens if chunk.usage else 0
        total_tokens = chunk.usage.total_tokens if chunk.usage else 0
        token_msg = f"Tokens: 输入 {in_tokens}, 输出 {out_tokens}, 合计 {total_tokens}"
        self.set_msg(f'AI 内容返回结束 ({token_msg})', level='hint')

    def set_msg(self, text, level='hint'):
        if level == 'hint':
            color = 'green'
        elif level == 'warn':
            color = 'yellow'
        else:  # err
            color = 'magenta'
        self._msg_label.setText(f'<span style="color: {color}">{text}</span>')

    def create_chat_context(self):
        return ChatContext(
            model=self._app.config.OPENAI_MODEL,
            client=self._app.ai.get_async_client(),
            messages=[{'role': 'system', 'content': QUERY_PROMPT}]
        )

    async def extract_and_play(self):
        await self._extract_and_play(EXTRACT_PROMPT)

    async def extract_10_and_play(self):
        await self._extract_and_play(f'{EXTRACT_PROMPT}\n随机提取最多10首即可')

    async def _extract_and_play(self, extract_prompt):
        """Main entry point for extracting and playing songs"""
        self._prepare_extract_context(extract_prompt)
        self.set_msg('正在让 AI 解析歌曲信息，这可能会花费一些时间...')
        try:
            stream = await self._chat_context.send_message()
            await self._process_extract_stream(stream)
        except Exception as e:
            self.set_msg(f'调用 AI 接口失败: {e}', level='err')
            logger.exception('AI request failed')

    def _prepare_extract_context(self, extract_prompt):
        """Prepare chat context for song extraction"""
        if self._chat_context is None:
            self.set_msg('没有对话上下文', level='err')
        else:
            self._add_message_to_history('user', extract_prompt)

    async def _process_extract_stream(self, stream):
        """Process the stream of extracted songs"""
        rr, rw, wtask = await a_handle_stream(stream)
        ok_count = 0
        fail_count = 0

        # 创建AI回复的标签
        ai_label = self._create_message_label('assistant', '')
        self._history_layout.addWidget(ai_label)
        content = ''
        try:
            while True:
                try:
                    line = await rr.readline()
                    line = line.decode('utf-8')
                    content += f'{line}\n'  # add newline
                    ai_label.setText(content)
                    self._scroll_to_bottom()
                    logger.debug(f'read a line: {line}')
                    if not line:
                        self.set_msg(f'解析结束，成功解析{ok_count}首歌曲，失败{fail_count}首歌。',
                                     level='hint')
                        break

                    try:
                        jline = json.loads(line)
                        title, artists = jline['title'], jline['artists']
                        artists_name = fmt_artists_names(artists)
                        song = create_dummy_brief_song(title, artists_name)
                    except Exception:
                        fail_count += 1
                        logger.exception(f'failed to parse a line: {line}')
                        self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                     level='yellow')
                        continue

                    ok_count += 1
                    self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                 level='hint')
                    self._app.playlist.add(song)
                    if ok_count == 1:
                        self._app.playlist.play_model(song)
                except Exception:
                    logger.exception('Error processing song')
                    break
        finally:
            assistant_message = {"role": "assistant", "content": content}
            self._chat_context.messages.append(assistant_message)
            chunk = await wtask
            self.show_tokens_usage(chunk)
            self._scroll_to_bottom()
            rw.close()
            await rw.wait_closed()
            self._editor.clear()

    def _scroll_to_bottom(self) -> None:
        """Scroll chat history to bottom."""
        self._history_area.verticalScrollBar().setValue(
            self._history_area.verticalScrollBar().maximum()
        )

    def clear_history(self):
        """Clear chat history"""
        while self._history_layout.count():
            item = self._history_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.set_msg('')
        self._chat_context = None

    def hide(self):
        self.clear_history()
        self.parent().hide()


def create_aichat_overlay(app: 'GuiApp', parent=None) -> AppOverlayContainer:
    """Create an overlay for the AI chat"""
    body = Body(app)
    overlay = AppOverlayContainer(app, body, parent=parent)
    return overlay


if __name__ == '__main__':
    import os
    from PyQt5.QtWidgets import QWidget
    from feeluown.gui.debug import simple_layout, mock_app

    with simple_layout(theme='dark') as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        app.config.OPENAI_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
        app.config.OPENAI_API_BASEURL = 'https://api.deepseek.com'
        app.config.OPENAI_MODEL = 'deepseek-chat'
        widget = create_aichat_overlay(app)
        widget.resize(600, 400)
        layout.addWidget(widget)
        widget.show()
        widget.body.set_msg('error', level='err')

        widget.body._chat_context = widget.body.create_chat_context()
        widget.body._add_message_to_history('user', '哈哈哈'*10)
        widget.body._add_message_to_history('xxx', '哈哈哈'*100)
