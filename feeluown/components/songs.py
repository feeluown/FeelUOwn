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
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QListView,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QWidget,
)

from feeluown.utils import parse_ms


class SongsTableModel(QAbstractTableModel):
    sections = ('', '歌曲标题', '时长', '歌手', '专辑')

    def __init__(self, songs):
        super().__init__()
        self.songs = songs

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, parent=QModelIndex()):
        return len(self.songs)

    def columnCount(self, _):
        return 5

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
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
                m, s = parse_ms(song.duration)
                duration = QTime(0, m, s)
                return duration.toString('mm:ss')
            elif index.column() == 3:
                return song.artists_name
            elif index.column() == 4:
                return song.album_name
        elif role == Qt.EditRole:
            return 1
        elif role == Qt.UserRole:
            return song
        return QVariant()


class ArtistsModel(QAbstractListModel):
    def __init__(self, artists):
        super().__init__()
        self.artists = artists

    def rowCount(self, parent=QModelIndex()):
        return len(self.artists)

    def data(self, index, role):
        artist = self.artists[index.row()]
        if role == Qt.DisplayRole:
            return artist.name
        elif role == Qt.UserRole:
            return artist
        elif role == Qt.SizeHintRole:
            return QSize(100, 30)
        return QVariant()


class SongOpsEditor(QWidget):
    """song editor for playlist table view"""

    def __init__(self, parent):
        super().__init__(parent)
        self.download_btn = QPushButton('↧', self)
        self.play_btn = QPushButton('☊', self)
        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self.play_btn)
        self._layout.addWidget(self.download_btn)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)


class ArtistsSelectionView(QListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog | Qt.FramelessWindowHint)
        self.setObjectName('artists_selection_view')


class SongsTableDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        self.view = parent

    def createEditor(self, parent, option, index):
        # Yeah, I'm a genius, again.
        if index.column() in (2, ):
            editor = SongOpsEditor(parent)
            editor.play_btn.clicked.connect(
                partial(self.closeEditor.emit, editor, QAbstractItemDelegate.SubmitModelCache))
            editor.download_btn.clicked.connect(
                partial(self.closeEditor.emit, editor, QAbstractItemDelegate.SubmitModelCache))
            editor.play_btn.clicked.connect(partial(self.view.play_song_needed.emit, index.data(role=Qt.UserRole)))
            return editor
        elif index.column() == 3:
            editor = ArtistsSelectionView(parent)
            editor.clicked.connect(partial(self.commitData.emit, editor))
            editor.move(parent.mapToGlobal(option.rect.bottomLeft()))
            editor.setFixedWidth(option.rect.width())
            return editor

    def setEditorData(self, editor, index):
        super().setEditorData(editor, index)
        if index.column() == 3:
            song = index.data(role=Qt.UserRole)
            model = ArtistsModel(song.artists)
            editor.setModel(model)
            editor.setCurrentIndex(QModelIndex())

    def setModelData(self, editor, model, index):
        if index.column() == 3:
            index = editor.currentIndex()
            if index.isValid():
                artist = index.data(Qt.UserRole)
                self.view.show_artist_needed.emit(artist)
        super().setModelData(editor, model, index)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        widths = (0.05, 0.3, 0.1, 0.2, 0.3)
        width = self.parent().width()
        w = int(width * widths[index.column()])
        return QSize(w, option.rect.height())

    def editorEvent(self, event, model, option, index):
        super().editorEvent(event, model, option, index)
        return False

    def updateEditorGeometry(self, editor, option, index):
        if index.column() == 3:
            pass
        else:
            super().updateEditorGeometry(editor, option, index)


class SongsTableView(QTableView):

    show_artist_needed = pyqtSignal([object])
    show_album_needed = pyqtSignal([object])
    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._previous_entered = None
        self._previous_clicked = None

        self.delegate = SongsTableDelegate(self)
        self.setItemDelegate(self.delegate)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # FIXME: PyQt5 seg fault
        #self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()

        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        #self.setSelectionMode(QAbstractItemView.NoSelection)
        #self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

        # self.entered.connect(self._on_entered)
        self.activated.connect(self._on_activated)

#    def _on_entered(self, index):
#        if self._previous_entered is not None:
#            self.closePersistentEditor(self._previous_entered)
#
#        # I'm genius!
#        if self.state() == QAbstractItemView.NoState and index.column() in (1, 2, ):
#            _index = self.model().createIndex(index.row(), 2)
#            self.openPersistentEditor(_index)
#            self._previous_entered = _index
#
    def _on_activated(self, index):
        if index.column() == 1:
            song = index.data(Qt.UserRole)
            self.play_song_needed.emit(song)
        elif index.column() == 3:
            song = index.data(Qt.UserRole)
            artists = song.artists
            if artists is not None:
                if len(artists) > 1:
                    self.edit(index)
                else:
                    self.show_artist_needed.emit(artists[0])
        elif index.column() == 4:
            song = index.data(Qt.UserRole)
            if song.album:
                self.show_album_needed.emit(song.album)

#    def leaveEvent(self, event):
#        super().leaveEvent(event)
#        if self._previous_entered is not None:
#            self.closePersistentEditor(self._previous_entered)
#
    def setModel(self, model):
        super().setModel(model)
        self.show_all_rows()

    def show_all_rows(self):
        for i in range(self.model().rowCount()):
            self.setRowHidden(i, False)

    def filter_row(self, text):
        # TODO: improve search algorithm
        if not text:
            self.show_all_rows()
            return
        if not self.model():
            return

        songs = self.model().songs
        for i, song in enumerate(songs):
            if text.lower() not in song.title.lower()\
                    and text not in song.album_name.lower()\
                    and text not in song.artists_name.lower():
                self.setRowHidden(i, True)
            else:
                self.setRowHidden(i, False)
