from enum import Enum
from functools import partial

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QSize,
    QTime,
    QVariant,
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QAction,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QListView,
    QMenu,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QWidget,
)


class CollectionItemsModel(QAbstractTableModel):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def flags(self, index):
        if index.column() == 1:
            return Qt.ItemIsSelectable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def rowCount(self, _=QModelIndex()):
        return len(self.items)

    def columnCount(self, _):
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        sections = ('地址', '描述')
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(sections):
                    return sections[section]
                return ''
        else:
            if role == Qt.DisplayRole:
                return section
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignLeft
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        item = self.items[index.row()]
        if role == Qt.DisplayRole:
            return item[index.column()]
        elif role == Qt.UserRole:
            return item
        return QVariant()


class TableDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        widths = (0.4, 0.6)
        width = self.parent().width()
        w = int(width * widths[index.column()])
        return QSize(w, option.rect.height())


class CollectionItemsView(QTableView):

    show_url = pyqtSignal([str])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.delegate = TableDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().hide()

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        item = index.data(Qt.UserRole)
        url, _ = item
        self.show_url.emit(url)
