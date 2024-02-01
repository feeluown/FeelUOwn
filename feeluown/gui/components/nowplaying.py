from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.utils.aio import run_afn
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.lyric import LyricView

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class NowplayingArtwork(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self._app = app
        self._inner = CoverLabelV2(app, self)
        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(0)
        self._layout.addWidget(self._inner)
        self._layout.addStretch(0)

    def on_metadata_changed(self, metadata):
        metadata = metadata or {}
        released = metadata.get('released', '')
        if released:
            self.setToolTip(f'专辑发行日期：{released}')
        else:
            self.setToolTip('')
        # Set song artwork.
        artwork = metadata.get('artwork', '')
        artwork_uid = metadata.get('uri', artwork)
        if artwork:
            run_afn(self._inner.show_cover, artwork, artwork_uid)
        else:
            self._inner.show_img(None)


class NowplayingLyricView(LyricView):
    """
    Let user zoom in/out.
    """

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.live_lyric.lyrics_changed.connect(self.on_lyric_changed, aioqueue=True)
        self._app.live_lyric.line_changed.connect(self.on_line_changed, weak=True)

        font = self.font()
        font.setPixelSize(17)
        self.setFont(font)
        self.viewport().setAutoFillBackground(False)

        self._alignment = Qt.AlignCenter
        self._highlight_font_size = 25
        self._item_spacing = 20

    def _create_item(self, line):
        item = super()._create_item(line)
        rect = QFontMetrics(item.font()).boundingRect(line)
        size = QSize(rect.width(), rect.height() + self._item_spacing)
        item.setData(Qt.UserRole, (line, size))
        item.setSizeHint(size)
        return item

    def on_item_changed(self, current, previous):
        super().on_item_changed(current, previous)

        if current:
            line, size_hint = current.data(Qt.UserRole)
            rect = QFontMetrics(current.font()).boundingRect(line)
            current.setSizeHint(
                QSize(
                    size_hint.width(),
                    rect.height() + self._item_spacing,
                )
            )

    def reset_item(self, item):
        super().reset_item(item)
        if item:
            item.setSizeHint(item.data(Qt.UserRole)[1])
