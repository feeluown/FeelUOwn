import logging

from PyQt5.QtCore import Qt
from .textlist import TextlistModel, TextlistView


logger = logging.getLogger(__name__)


class MyMusicModel(TextlistModel):

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.DisplayRole:
            return item.text
        return super().data(index, role)


class MyMusicView(TextlistView):

    def __init__(self, parent):
        super().__init__(parent)
        self.clicked.connect(
            lambda index: index.data(role=Qt.UserRole).clicked.emit())
