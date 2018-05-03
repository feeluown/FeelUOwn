from functools import partial

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractTableModel,
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
    QInputDialog,
    QItemDelegate,
    QListView,
    QPushButton,
    QStyledItemDelegate,
    QSpinBox,
    QTableView,
    QTableWidget,
    QWidget,
)

from feeluown.utils import parse_ms


class PlaylistTableModel(QAbstractTableModel):
    sections = ('', '歌曲标题', '时长', '歌手', '专辑')

    def __init__(self, songs):
        super().__init__()
        self.songs = songs

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, _):
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


class PlaylistTableDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        self.table = parent

    def createEditor(self, parent, option, index):
        if index.column() in (1, 2):
            editor = SongOpsEditor(parent)
            editor.play_btn.clicked.connect(
                partial(self.closeEditor.emit, editor, QAbstractItemDelegate.SubmitModelCache))
            editor.download_btn.clicked.connect(
                partial(self.closeEditor.emit, editor, QAbstractItemDelegate.SubmitModelCache))
            editor.play_btn.clicked.connect(partial(self.table.play_song_needed.emit, index.data(role=Qt.UserRole)))
            return editor

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        widths = (0.05, 0.3, 0.1, 0.2, 0.3)
        width = self.parent().width()
        w = int(width * widths[index.column()])
        return QSize(w, option.rect.height())


class PlaylistTableView(QTableView):

    style_fmt = """
    QHeaderView {{
        color: {foreground};
        background: transparent;
        font-size: 14px;
    }}
    QHeaderView::section:horizontal {{
        height: 24px;
        background: transparent;
        border-top: 1px;
        border-right: 1px;
        border-bottom: 1px;
        border-color: {color7_light};
        color: {color7_light};
        border-style: solid;
        padding-left: 5px;
    }}
    QTableView QTableCornerButton::section {{
        background: transparent;
    }}
    QTableView {{
        font-size: 13px;
        background: transparent;
        alternate-background-color: rgba(0, 0, 0, 0.09);
        selection-background-color: transparent;
        color: {foreground};
        outline: none;
        border: 0px;
    }}
    QTableView::item {{
        background: transparent;
        color: {foreground};
    }}
    QTableView::item:hover {{
    }}
    QTableView::item:focus {{
        outline: none;
    }}
    QTableView::item:selected {{
        color: {color3};
    }}
    QTableView QWidget {{
        height: 100%;
    }}
    QTableView QPushButton {{
        font-size: 18px;
        background: {background_light};
        color: {foreground};
        border-radius: 3px;
    }}
    QTableView QPushButton:hover {{
        font-size: 20px;
        color: {color4};
    }}
    """

    show_artist_needed = pyqtSignal([object])
    show_album_needed = pyqtSignal([object])
    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._entered_previous = None

        self.clicked.connect(self._on_click)
        self.doubleClicked.connect(self._on_db_click)
        self.delegate = PlaylistTableDelegate(self)
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
        self.entered.connect(self._on_entered)
        self.setObjectName('playlist_table')

    def _on_click(self, index):
        song = self.model().data(index, Qt.UserRole)

        # emit show_artist_needed signal
        if index.column() == 3:
            if len(song.artists) > 1:
                dialog = QInputDialog(self)
                dialog.setOptions(QInputDialog.UseListViewForComboBoxItems)
                dialog.setComboBoxItems([artist.name for artist in song.artists])
                if dialog.exec():
                    name = dialog.textValue()
                    for artist in song.artists:
                        if artist.name == name:
                            self.show_artist_needed.emit(artist)
            elif len(song.artists) == 1:
                self.show_artist_needed.emit(song.artists[0])

        elif index.column() == 4 and song.album:
            self.show_album_needed.emit(song.album)

    def _on_db_click(self, index):
        if index.column() == 1:
            song = self.model().data(index, Qt.UserRole)
            self.play_song_needed.emit(song)
        elif index.column() == 2:
            self.openPersistentEditor(index)

    def _on_entered(self, index):
        if self._entered_previous is not None:
            self.closePersistentEditor(self._entered_previous)

        # I'm genius!
        if self.state() == QAbstractItemView.NoState:
            _index = self.model().createIndex(index.row(), 2)
            self.openPersistentEditor(_index)
            self._entered_previous = _index

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._entered_previous is not None:
            self.closePersistentEditor(self._entered_previous)
