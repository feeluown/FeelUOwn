from collections import deque

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    QModelIndex,
    QSize,
    Qt,
    QVariant,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QListView,
    QSizePolicy,
)

from fuocore import ModelType


class HistoriesModel(QAbstractListModel):
    def __init__(self, size=5, parent=None):
        super().__init__(parent)
        self._size = size
        self._models = deque()

    def append(self, model):
        # TODO: change strategy to LRU
        curlen = len(self._models)
        if model in self._models:
            self.beginInsertRows(QModelIndex(), curlen - 2, curlen - 1)
            self._models.remove(model)
            self._models.append(model)
            self.endInsertRows()
            return

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

        # latest first
        model = self._models[len(self._models) - row - 1]
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


class HistoriesView(QListView):
    """显示最近浏览的播放列表、歌手、专辑等"""

    show_model = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.NoSelection)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        model = index.data(role=Qt.UserRole)
        self.show_model.emit(model)

    def sizeHint(self):
        return QSize(self.width(), 100)

    def currentChanged(self, current, previous):
        """让最近浏览的元素流畅的显示在列表最上方"""
        first = self.model().index(0, 0)
        super().currentChanged(first, previous)
