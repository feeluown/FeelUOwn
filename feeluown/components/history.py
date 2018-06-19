from collections import deque

from PyQt5.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QSize,
    Qt,
    QVariant,
)
from PyQt5.QtWidgets import (
    QListView,
    QSizePolicy,
)

from fuocore import ModelType


class HistoryModel(QAbstractListModel):
    def __init__(self, size=5, parent=None):
        super().__init__(parent)
        self._size = size
        self._models = deque()

    def append(self, model):
        # TODO: change strategy to LRU
        curlen = len(self._models)
        if curlen > self._size:
            self.beginInsertRows(QModelIndex(), curlen - 1, curlen)
            self._models.popleft()
        else:
            self.beginInsertRows(QModelIndex(), curlen, curlen + 1)
        self._models.append(model)
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self._models)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self._models) or row < 0:
            return QVariant()

        model = self._models[row]
        if role == Qt.DisplayRole:
            if model.type_ == ModelType.song:
                return model.title
            elif model.type_ in (ModelType.playlist,
                                 ModelType.artist,
                                 ModelType.album):
                return model.name
            else:
                return str(model)
        elif role == Qt.UserRole:
            return model
        return QVariant()


class HistoryView(QListView):
    def __init__(self, parent):
        super().__init__(parent)
