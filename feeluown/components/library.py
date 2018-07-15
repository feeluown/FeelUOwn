"""
FIXME: 感觉这个 component 设计有点问题，做的事情太多，得拆！
"""

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
    def __init__(self, provider, search=None, on_click=None,
                 icon='♬ ', desc='', **kwargs):
        self.identifier = provider.identifier
        self.name = provider.name
        self.icon = icon
        self.desc = desc
        self.search = search
        self._on_click = on_click


class LibrariesModel(QAbstractListModel):
    def __init__(self, libraries=None, parent=None):
        super().__init__(parent)
        self._libraries = libraries or []

    def search(self, keyword):
        songs = []
        for library in self._libraries:
            if not library.search:
                continue
            result = library.search(keyword=keyword)
            _songs = list(result.songs[:20])
            songs.extend(_songs)
        return songs

    def register(self, library):
        self._libraries.append(library)

    def __getitem__(self, index):
        return self._libraries[index]

    def rowCount(self, parent=QModelIndex()):
        return len(self._libraries)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self._libraries) or row < 0:
            return QVariant()

        library = self._libraries[row]
        if role == Qt.DisplayRole:
            return library.icon + ' ' + library.name
        elif role == Qt.ToolTipRole:
            return library.desc
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
        if library._on_click:
            library._on_click()

    def sizeHint(self):
        height = 10
        if self.model().rowCount() > 0:
            height = self.model().rowCount() * self.sizeHintForRow(0)
        return QSize(self.width(), height)
