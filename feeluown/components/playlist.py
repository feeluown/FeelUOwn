from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractTableModel,
    QAbstractListModel,
    Qt,
    QTime,
    QVariant,
)
from PyQt5.QtWidgets import (
    QListView,
    QComboBox,
    QItemDelegate,
    QSpinBox,
)

from feeluown.components import SongsTable
from feeluown.utils import parse_ms


class ArtistListModel(QAbstractListModel):
    def __init__(self, artists):
        super().__init__()
        self.artists = artists

    def rowCount(self, _):
        return len(self.artists)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self.artists):
            return QVariant()
        if role == Qt.DisplayRole:
            return self.artists[index.row()].name
        return ''


class ArtistsComboBox(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)

        self.activated.connect(self._on_activated)

    def _on_activated(self, data):
        print(data)


class PlaylistTableModel(QAbstractTableModel):
    sections = ('', '歌曲标题', '歌手', '专辑', '时长')

    def __init__(self, songs):
        super().__init__()
        self.songs = songs

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def rowCount(self, _):
        return len(self.songs)

    def columnCount(self, _):
        return 5

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            if section < len(self.sections):
                return self.sections[section]
            return ''

        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self.songs) or index.row() < 0:
            return QVariant()

        song = self.songs[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return ''
            elif index.column() == 1:
                return song.title
            elif index.column() == 2:
                return song.artists_name
            elif index.column() == 3:
                return song.album_name
            elif index.column() == 4:
                m, s = parse_ms(song.duration)
                duration = QTime(0, m, s)
                return duration.toString()
        elif role == Qt.EditRole:
            return 1
        elif role == Qt.UserRole:
            return song
        return QVariant()


class PlaylistTableView(SongsTable):

    show_artist_needed = pyqtSignal([object])
    show_album_needed = pyqtSignal([object])
    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.clicked.connect(self._on_click)
        # self.doubleClicked.connect(self._on_db_click)

        # self.delegate = ArtistsDelegate(self)
        #self.delegate = SpinBoxDelegate(self)
        #self.setItemDelegate(self.delegate)

    def _on_click(self, index):
        song = self.model().data(index, Qt.UserRole)
        if index.column() == 2:
            if len(song.artists) > 1:
                combobox = ArtistsComboBox(self)
                combobox.setModel(ArtistListModel(song.artists))
                self.setIndexWidget(index, combobox)
                self.setIndexWidget(index, None)
            elif len(song.artists) == 1:
                self.show_artist_needed.emit(song.artists[0])
        elif index.column() == 3 and song.album:
            self.show_album_needed.emit(song.album)

    def _on_db_click(self, index):
        if index.column() == 1:
            song = self.model().data(index, Qt.UserRole)
            self.play_song_needed.emit(song)
