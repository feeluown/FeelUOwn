from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import QPainter, QPalette, QColor
from PyQt5.QtWidgets import QLabel, QSizePolicy, QMenu, QVBoxLayout, QWidget

from feeluown.player import PlaylistPlayModelStage
from feeluown.library import fmt_artists_names
from feeluown.gui.components import SongMenuInitializer
from feeluown.gui.helpers import elided_text

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class LineSongLabel(QLabel):
    """Show song info in one line (with limited width)."""

    default_text = '...'

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(text=self.default_text, parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._app = app

        # TODO: we can create a label class that roll the text when
        # the text is longer than the label width
        self._timer = QTimer()
        self._txt = self._raw_text = self.default_text
        self._text_rect = self.fontMetrics().boundingRect(self._raw_text)
        # text's position, keep changing to make text roll
        self._pos = 0
        self._timer.timeout.connect(self.change_text_position)

        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True
        )
        self._app.playlist.play_model_stage_changed.connect(
            self.on_play_model_stage_changed, aioqueue=True
        )

    def on_metadata_changed(self, metadata):
        if not metadata:
            self.setText('...')
            return

        # Set main text.
        text = metadata.get('title', '')
        if text:
            artists = metadata.get('artists', [])
            if artists:
                # FIXME: use _get_artists_name
                text += f" • {','.join(artists)}"
        self.setText(text)

    def on_play_model_stage_changed(self, stage):
        if stage == PlaylistPlayModelStage.prepare_media:
            self.setText('正在获取歌曲播放链接...')
        elif stage == PlaylistPlayModelStage.find_standby_by_mv:
            self.setText('正在获取音乐的视频播放链接...')
        elif stage == PlaylistPlayModelStage.find_standby:
            self.setText('尝试寻找备用播放链接...')
        elif stage == PlaylistPlayModelStage.prepare_metadata:
            self.setText('尝试获取完整的歌曲元信息...')
        elif stage == PlaylistPlayModelStage.load_media:
            self.setText('正在加载歌曲资源...')

    def change_text_position(self):
        if not self.parent().isVisible():  # type: ignore
            self._timer.stop()
            self._pos = 0
            return
        if self._text_rect.width() + self._pos > 0:
            # control the speed of rolling
            self._pos -= 5
        else:
            self._pos = self.width()
        self.update()

    def setText(self, text):
        self._txt = self._raw_text = text
        self._text_rect = self.fontMetrics().boundingRect(self._raw_text)
        self._pos = 0
        self.update()

    def enterEvent(self, event):
        # we do not compare text_rect with self_rect here because of
        # https://github.com/feeluown/FeelUOwn/pull/425#discussion_r536817226
        # TODO: find out why
        if self._txt != self._raw_text:
            # decrease to make rolling more fluent
            self._timer.start(150)

    def leaveEvent(self, event):
        self._timer.stop()
        self._pos = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(QPalette.Text))

        if self._timer.isActive():
            self._txt = self._raw_text
        else:
            self._txt = self.fontMetrics().elidedText(
                self._raw_text, Qt.ElideRight, self.width()
            )

        painter.drawText(
            QRect(self._pos, 0,
                  self.width() - self._pos, self.height()),
            Qt.AlignLeft | Qt.AlignVCenter, self._txt
        )  # type: ignore[call-overload]

    def contextMenuEvent(self, e):
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        SongMenuInitializer(self._app, song).apply(menu)
        menu.exec(e.globalPos())


class TwoLineSongLabel(QWidget):
    default_text = '...'

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._title_label = QLabel()
        self._subtitle_label = QLabel()

        palette = self._subtitle_label.palette()
        palette.setColor(QPalette.Text, QColor('grey'))
        palette.setColor(QPalette.Foreground, QColor('Grey'))
        self._subtitle_label.setPalette(palette)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)
        self._layout.addWidget(self._title_label)
        self._layout.addWidget(self._subtitle_label)
        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True
        )

        font = self.font()
        font.setPixelSize(25)
        font.setBold(True)
        self._title_label.setFont(font)
        font.setPixelSize(20)
        font.setBold(False)
        self._subtitle_label.setFont(font)

    def on_metadata_changed(self, metadata):
        if not metadata:
            self._title_label.setText('...')
            return

        # Set main text.
        title = metadata.get('title', '')
        if title:
            artists = metadata.get('artists', [])
            if artists:
                # FIXME: use _get_artists_name
                subtitle = fmt_artists_names(artists)
                self._subtitle_label.setText(
                    elided_text(
                        subtitle, self._subtitle_label.width(),
                        self._subtitle_label.font()
                    )
                )
        self._title_label.setText(
            elided_text(title, self._title_label.width(), self._title_label.font())
        )
