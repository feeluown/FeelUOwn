import logging

from PyQt5.QtCore import (
    QAbstractListModel,
    Qt,
    QModelIndex,
    QSize,
    QVariant,
)
from PyQt5.QtWidgets import QListView


logger = logging.getLogger(__name__)


class TextlistModel(QAbstractListModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._items = []

    @property
    def items(self):
        return self._items

    def add(self, item):
        start = len(self._items)
        end = start + 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._items.append(item)
        self.endInsertRows()

    def remove(self, item):
        row = self._items.index(item)
        self.beginRemoveRows(QModelIndex(), row, row + 1)
        self._items.remove(item)
        self.endRemoveRows()

    def clear(self):
        total_length = len(self.items)
        self.beginRemoveRows(QModelIndex(), 0, total_length - 1)
        self._items = []
        self.endRemoveRows()

    def rowCount(self, _=QModelIndex()):
        return len(self.items)

    def flags(self, index):  # pylint: disable=no-self-use
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        item = self.items[row]
        if role == Qt.UserRole:
            return item
        return QVariant()

    def __len__(self):
        return len(self._items)


class TextlistView(QListView):

    def __init__(self, parent):
        super().__init__(parent)

        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, e):  # pylint: disable=no-self-use
        e.ignore()

    def sizeHint(self):
        height = 10
        for i in range(0, self.model().rowCount()):
            height += self.sizeHintForRow(i)
        return QSize(self.width(), height)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self.setFixedHeight(self.sizeHint().height())

    def rowsAboutToBeRemoved(self, parent, start, end):
        super().rowsAboutToBeRemoved(parent, start, end)
        self.setFixedHeight(self.sizeHint().height())
