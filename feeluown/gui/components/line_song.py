from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import QFontMetrics, QPainter, QPalette
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy, QMenu

from feeluown.gui.components import SongMenuInitializer

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
        self._font_metrics = QFontMetrics(QApplication.font())
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
        # text's position, keep changing to make text roll
        self._pos = 0
        self._timer.timeout.connect(self.change_text_position)

        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True)
        self._app.playlist.play_model_handling.connect(
            self.on_play_model_handling, aioqueue=True)

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
                text += f" - {','.join(artists)}"
        self.setText(text)

    def on_play_model_handling(self):
        self.setText('正在加载歌曲...')

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
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
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
        painter.setFont(QApplication.font())
        painter.setPen(self.palette().color(QPalette.Text))

        if self._timer.isActive():
            self._txt = self._raw_text
        else:
            self._txt = self._font_metrics.elidedText(
                self._raw_text, Qt.ElideRight, self.width())

        painter.drawText(
            QRect(self._pos, 0, self.width() - self._pos, self.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            self._txt
        )  # type: ignore[call-overload]

    def contextMenuEvent(self, e):
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        SongMenuInitializer(self._app, song).apply(menu)
        menu.exec(e.globalPos())
