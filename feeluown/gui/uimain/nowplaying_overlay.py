from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import QEvent, QSize
from PyQt5.QtGui import QResizeEvent, QKeySequence
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QShortcut

from feeluown.gui.components.btns import MediaButtons
from feeluown.gui.components.nowplaying import NowplayingArtwork, NowplayingLyricView
from feeluown.gui.components.line_song import LineSongLabel

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class PlayerPanel(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self.artwork_label = NowplayingArtwork(app, self)
        self.line_song_label = LineSongLabel(app, self)
        self.media_btns = MediaButtons(app, parent=self)

        font = self.line_song_label.font()
        font.setPixelSize(25)
        font.setBold(True)
        self.line_song_label.setFont(font)
        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout(self)
        # Put the cover_label in a vboxlayout and add strech around it,
        # so that cover_label's sizehint is respected.
        self._layout.addWidget(self.line_song_label)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.artwork_label)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.media_btns)
        self._layout.addSpacing(0)

    def sizeHint(self):
        return QSize(500, 400)


class NowplayingOverlay(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.installEventFilter(self)

        self.player_panel = PlayerPanel(app, parent=self)
        self.lyric_view = NowplayingLyricView(app, self)
        self._layout = QHBoxLayout(self)

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)
        self.setup_ui()
        self.setAutoFillBackground(True)

    def setup_ui(self):
        self._layout.addWidget(self.player_panel)
        self._layout.addWidget(self.lyric_view)

    def show(self):
        self.resize(self._app.size())
        super().show()

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False
