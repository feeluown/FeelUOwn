import logging
from PyQt5.QtCore import pyqtSignal, Qt

from .textlist import TextlistModel, TextlistView


logger = logging.getLogger(__name__)


class CollectionsModel(TextlistModel):
    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.DisplayRole:
            return '◎  ' + item.name
        if role == Qt.ToolTipRole:
            return item.fpath
        return super().data(index, role)


class CollectionsView(TextlistView):
    show_collection = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        collection = index.data(role=Qt.UserRole)
        self.show_collection.emit(collection)
