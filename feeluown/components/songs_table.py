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

from feeluown.utils import parse_ms
from feeluown.mimedata import ModelMimeData
from feeluown.helpers import use_mac_theme


class Column(Enum):
    song = 0
    source = 1
    duration = 2
    artist = 3
    album = 4


class SongsTableModel(QAbstractTableModel):
    def __init__(self, songs, source_name_map=None):
        super().__init__()
        self.songs = songs
        self._source_set = set()

        # XXX: icon should be a str (charactor symbol)
        self._source_name_map = source_name_map or {}
        self._initialize()

    def _initialize(self):
        for song in self.songs:
            self._source_set.add(song.source)

    def flags(self, index):
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        if index.column() in (2, ):
            return Qt.ItemIsSelectable
        elif index.column() in (0, ):
            return Qt.ItemIsSelectable
        elif index.column() == 1:
            return flags | Qt.ItemIsDragEnabled
        return flags

    def rowCount(self, parent=QModelIndex()):
        return len(self.songs)

    def columnCount(self, _):
        return 5

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        sections = ('来源', '歌曲标题', '时长', '歌手', '专辑')
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(sections):
                    return sections[section]
                return ''
        else:
            if role == Qt.DisplayRole:
                return section
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignRight
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self.songs) or index.row() < 0:
            return QVariant()

        song = self.songs[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self._source_name_map.get(song.source, '').strip()
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
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignCenter | Qt.AlignBaseline
        elif role == Qt.EditRole:
            return 1
        elif role == Qt.UserRole:
            return song
        return QVariant()

    def mimeData(self, indexes):
        if len(indexes) == 1:
            index = indexes[0]
            song = index.data(Qt.UserRole)
            return ModelMimeData(song)



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
        widths = (0.1, 0.3, 0.1, 0.2, 0.3)
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

    # 之后或许可以改成 row_deleted，row_deleted 更抽象，
    # 而 song_deleted 更具体，方便以后修改设计。
    song_deleted = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.delegate = SongsTableDelegate(self)
        self.setItemDelegate(self.delegate)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # FIXME: PyQt5 seg fault
        # self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # macOS 的滚动条可以自动隐藏
        if not use_mac_theme():
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.setFrameShape(QFrame.NoFrame)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()

        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        # self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.activated.connect(self._on_activated)

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

    def contextMenuEvent(self, event):
        menu = QMenu()
        index = self.indexAt(event.pos())
        self.selectRow(index.row())
        song = self.model().data(index, Qt.UserRole)
        remove_song_action = QAction('移除歌曲', menu)
        remove_song_action.triggered.connect(partial(self.song_deleted.emit, song))
        menu.addAction(remove_song_action)
        menu.exec(event.globalPos())
