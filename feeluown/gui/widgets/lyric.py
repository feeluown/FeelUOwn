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
            item = QListWidgetItem(line)
            if i == lyric.current_index:
                self.setCurrentItem(item)
            self.addItem(item)

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
            font.setPixelSize(18)
            current.setFont(font)

    def reset_item(self, item):
        if item:
            item.setFont(self.font())
