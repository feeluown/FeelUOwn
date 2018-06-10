from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    Qt,
    QSize,
    QTime,
    QVariant,
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


class PlaylistsModel(QAbstractListModel):
    def __init__(self, playlists, parent):
        super().__init__(parent)
        self.playlists = playlists

    def rowCount(self, _):
        return len(self.playlists)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # XXX: 实际不产生任何效果
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return '播放列表'
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self.playlists) or row < 0:
            return QVariant()

        playlist = self.playlists[row]
        if role == Qt.DisplayRole:
            return '♬  ' + playlist.name
        elif role == Qt.UserRole:
            return playlist
        return QVariant()


class PlaylistsView(QListView):

    show_playlist = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        playlist = index.data(role=Qt.UserRole)
        self.show_playlist.emit(playlist)
