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


class LibraryModel(object):
    def __init__(self, identifier, name, load_cb, icon=None, **kwargs):
        self.identifier = identifier
        self.name = name
        self.load_cb = load_cb
        self.icon = icon or '♬ '


class LibrariesModel(QAbstractListModel):
    def __init__(self, libraries=None, parent=None):
        super().__init__(parent)
        self.libraries = libraries or []

    def add_library(self, library):
        self.libraries.append(library)

    def rowCount(self, parent=QModelIndex()):
        return len(self.libraries)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self.libraries) or row < 0:
            return QVariant()

        library = self.libraries[row]
        if role == Qt.DisplayRole:
            return library.icon + ' ' + library.name
        elif role == Qt.UserRole:
            return library
        return QVariant()


class LibrariesView(QListView):
    def __init__(self, parent):
        super().__init__(parent)

        self.setMinimumHeight(100)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        library = index.data(role=Qt.UserRole)
        library.load_cb()

    def sizeHint(self):
        height = 10
        if self.model().rowCount() > 0:
            height = self.model().rowCount() * self.sizeHintForRow(0)
        return QSize(self.width(), height)
