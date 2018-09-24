import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    Qt,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    QTimer,
    QVariant,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QFontMetrics,
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QItemDelegate,
    QListView,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QSpinBox,
    QTableView,
    QTableWidget,
    QWidget,
)

logger = logging.getLogger(__name__)


class MyMusicItem(object):
    def __init__(self, name, on_click):
        self.name = name
        self.on_click = on_click


class MyMusicModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def add(self, item):
        length = len(self._items)
        self.beginInsertRows(QModelIndex(), length, length + 1)
        self._items.append(item)
        self.endInsertRows()

    def clear(self):
        total_length = len(self._items)
        self.beginRemoveRows(QModelIndex(), 0, total_length - 1)
        self._items = []
        self.endRemoveRows()

    def rowCount(self, _=QModelIndex()):
        return len(self._items)

    def flags(self, index):  # pylint: disable=no-self-use
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self._items) or row < 0:
            return QVariant()
        item = self._items[row]
        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.UserRole:
            return item
        return QVariant()


class MyMusicView(QListView):

    def __init__(self, parent):
        super().__init__(parent)

        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        item = index.data(role=Qt.UserRole)
        item.on_click()

    def sizeHint(self):
        count = self.model().rowCount()
        height = self.sizeHintForRow(0) * count
        return QSize(self.width(), height)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self.setFixedHeight(self.sizeHint().height())

    def rowsAboutToBeRemoved(self, parent, start, end):
        super().rowsAboutToBeRemoved(parent, start ,end)
        self.setFixedHeight(self.sizeHint().height())
