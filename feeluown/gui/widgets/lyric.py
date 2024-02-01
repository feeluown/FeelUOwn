from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QFrame

from feeluown.player import Lyric


class LyricView(QListWidget):
    """Scollable lyrics list view.

    Two slots can be connected:
    1. on_line_changed
    2. on_lyric_changed
    """

    def __init__(self, parent):
        super().__init__(parent)

        self._lyric = None
        self._alignment = Qt.AlignLeft
        self._highlight_font_size = 18

        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrap(True)

        self.currentItemChanged.connect(self.on_item_changed)

    def set_lyric(self, lyric: Lyric):
        self.clear()
        self._lyric = lyric
        if lyric is None:
            return

        for i, line in enumerate(lyric.lines):
            item = self._create_item(line)
            if i == lyric.current_index:
                self.setCurrentItem(item)
            self.addItem(item)

    def _create_item(self, line):
        item = QListWidgetItem(line)
        item.setTextAlignment(self._alignment)
        return item

    def clear(self):
        super().clear()
        self._lyric = None

    def on_line_changed(self, _):
        if self._lyric is None:
            return
        index = self._lyric.current_index
        if index is not None:
            item = self.item(index)
            self.setCurrentItem(item)
            self.scrollToItem(item, QAbstractItemView.PositionAtCenter)
        else:
            self.setCurrentItem(None)

    def on_lyric_changed(self, lyric, _, *__):
        self.set_lyric(lyric)

    def on_item_changed(self, current, previous):
        self.reset_item(previous)
        if current:
            font = current.font()
            font.setPixelSize(self._highlight_font_size)
            current.setFont(font)

    def reset_item(self, item):
        if item:
            item.setFont(self.font())
