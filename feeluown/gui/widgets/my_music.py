import logging

from PyQt6.QtCore import Qt
from .textlist import TextlistModel, TextlistView


logger = logging.getLogger(__name__)


class MyMusicModel(TextlistModel):
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.ItemDataRole.DisplayRole:
            return item.text
        return super().data(index, role)


class MyMusicView(TextlistView):
    def __init__(self, parent):
        super().__init__(parent)
        self.clicked.connect(
            lambda index: index.data(role=Qt.ItemDataRole.UserRole).clicked.emit()
        )
