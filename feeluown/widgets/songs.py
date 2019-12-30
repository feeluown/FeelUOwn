from enum import IntEnum
from functools import partial

from PyQt5.QtCore import (
    pyqtSignal, Qt, QVariant, QEvent,
    QAbstractTableModel, QAbstractListModel, QModelIndex,
    QSize, QRect, QPoint,
)
from PyQt5.QtGui import QPainter, QPalette, QPen, QMouseEvent
from PyQt5.QtWidgets import (
    QAction, QFrame, QHBoxLayout, QAbstractItemView, QHeaderView,
    QApplication, QPushButton, QTableView, QWidget, QMenu, QListView,
    QStyle, QSizePolicy, QStyleOptionButton, QStyledItemDelegate,
)

from fuocore.models import ModelExistence
from feeluown.mimedata import ModelMimeData


class Column(IntEnum):
    index = 0
    song = 2
    source = 1
    duration = 3
    artist = 4
    album = 5


class SongListModel(QAbstractListModel):
    def __init__(self, reader, parent=None):
        super().__init__(parent)

        self._songs = []  # songs read from reader
        self._can_fetch_more = True
        self._reader = reader

    def rowCount(self, _=QModelIndex()):
        return len(self._songs)

    def fetchMore(self, _=QModelIndex()):
        fetched, total = 0, 30
        songs = []
        for song in self._reader:
            fetched += 1
            songs.append(song)
            if fetched >= total:
                break
        else:
            self._can_fetch_more = False
        begin = len(self._songs)
        self.beginInsertRows(QModelIndex(), begin, begin + len(songs) - 1)
        self._songs.extend(songs)
        self.endInsertRows()

    def canFetchMore(self, _):
        return self._can_fetch_more

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            return self._songs[row].title_display
        elif role == Qt.UserRole:
            return self._songs[row]
        return None


class SongListDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent=parent)

        # the rect.x the number text
        self.number_rect_x = 40
        self.play_btn_pressed = False

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(140)
        text_pen = QPen(text_color)
        non_text_pen = QPen(non_text_color)
        hl_text_pen = QPen(option.palette.color(QPalette.HighlightedText))
        if option.state & QStyle.State_Selected:
            painter.setPen(hl_text_pen)
        else:
            painter.setPen(text_pen)

        song = index.data(Qt.UserRole)
        top = option.rect.top()
        bottom = option.rect.bottom()
        no_x = self.number_rect_x
        duration_x = option.rect.topRight().x() - 50
        no_bottom_right = QPoint(no_x, bottom)
        text_top_left = QPoint(no_x + 10, top)
        text_bottom_right = QPoint(duration_x, bottom)
        duration_top_left = QPoint(duration_x, top)
        no_rect = QRect(option.rect.topLeft(), no_bottom_right)
        text_rect = QRect(text_top_left, text_bottom_right)
        duration_rect = QRect(duration_top_left, option.rect.bottomRight())
        painter.drawText(text_rect, Qt.AlignVCenter, song.title_display)

        painter.setPen(non_text_pen)
        if option.state & QStyle.State_MouseOver:
            opt = QStyleOptionButton()
            opt.text = '►'
            opt.palette = option.palette
            opt.state = QStyle.State_Enabled
            opt.rect = no_rect
            QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)
        else:
            painter.drawText(no_rect, Qt.AlignCenter, str(index.row() + 1))
        painter.drawText(duration_rect, Qt.AlignCenter, song.duration_ms_display)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            no_bottom_right = QPoint(self.number_rect_x, option.rect.bottom())
            no_rect = QRect(option.rect.topLeft(), no_bottom_right)
            mouse_event = QMouseEvent(event)
            if no_rect.contains(mouse_event.pos()):
                if event.type() == QEvent.MouseButtonPress:
                    self.play_btn_pressed = True
                if event.type() == QEvent.MouseButtonRelease:
                    if self.play_btn_pressed is True:
                        self.parent().play_song_needed.emit(index.data(Qt.UserRole))
            if event.type() == QEvent.MouseButtonRelease:
                self.play_btn_pressed = False
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.isValid():
            return QSize(size.width(), 36)
        return size


class SongListView(QListView):

    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.delegate = SongListDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        self.play_song_needed.emit(index.data(Qt.UserRole))


class SongsTableModel(QAbstractTableModel):
    def __init__(self, songs=None, source_name_map=None, songs_g=None, parent=None):
        """

        :param songs: 歌曲列表
        :param songs_g: 歌曲列表生成器（当歌曲列表生成器不为 None 时，忽略 songs 参数）
        """
        super().__init__(parent)
        self.songs_g = songs_g
        self.songs = (songs or []) if songs_g is None else []
        self._source_set = set()
        self._can_fetch_more = self.songs_g is not None
        self._source_name_map = source_name_map or {}
        self._initialize()

    def _initialize(self):
        for song in self.songs:
            self._source_set.add(song.source)

    def canFetchMore(self, _):
        return self._can_fetch_more

    def fetchMore(self, _):
        songs = []
        for _ in range(len(self.songs), len(self.songs) + 30):
            try:
                song = next(self.songs_g)
            except StopIteration:
                self._can_fetch_more = False
                break
            else:
                songs.append(song)
        begin = len(self.songs)
        self.beginInsertRows(QModelIndex(), begin, begin + len(songs) - 1)
        self.songs.extend(songs)
        self.endInsertRows()

    def flags(self, index):
        song = index.data(Qt.UserRole)
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        if song and song.exists == ModelExistence.no or \
           index.column() in (Column.source, Column.index, Column.duration):
            return Qt.ItemIsSelectable
        if index.column() == Column.song:
            return flags | Qt.ItemIsDragEnabled
        return flags

    def rowCount(self, parent=QModelIndex()):
        return len(self.songs)

    def columnCount(self, _):
        return 6

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        sections = ('', '来源', '歌曲标题', '时长', '歌手', '专辑')
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(sections):
                    return sections[section]
                return ''
            elif role == Qt.SizeHintRole:
                # we set height to 25 since the header can be short under macOS.
                # HELP: set height to fixed value manually is not so elegant
                height = 25
                # HELP: the last column width percent should be 1-others.
                # 0.3 may cause the header wider than the tableview
                # (for example, under KDE Plasma 5.15.5 with QT 5.12.3),
                # which is unacceptable. In fact, the width percent can be 0.2
                # or even less since we have enabled StretchLastSection.
                widths = (0.05, 0.1, 0.25, 0.1, 0.2, 0.2)
                width = self.parent().width()
                w = int(width * widths[section])
                return QSize(w, height)
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
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if index.column() == Column.index:
                return index.row() + 1
            elif index.column() == Column.source:
                return self._source_name_map.get(song.source, '').strip()
            elif index.column() == Column.song:
                return song.title_display
            elif index.column() == Column.duration:
                return song.duration_ms_display
            elif index.column() == Column.artist:
                return song.artists_name_display
            elif index.column() == Column.album:
                return song.album_name_display
        elif role == Qt.TextAlignmentRole:
            if index.column() == Column.index:
                return Qt.AlignCenter | Qt.AlignVCenter
            elif index.column() == Column.source:
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
        if index.column() == Column.artist:
            editor = ArtistsSelectionView(parent)
            editor.clicked.connect(partial(self.commitData.emit, editor))
            editor.move(parent.mapToGlobal(option.rect.bottomLeft()))
            editor.setFixedWidth(option.rect.width())
            return editor

    def setEditorData(self, editor, index):
        super().setEditorData(editor, index)
        if index.column() == Column.artist:
            song = index.data(role=Qt.UserRole)
            model = ArtistsModel(song.artists)
            editor.setModel(model)
            editor.setCurrentIndex(QModelIndex())

    def setModelData(self, editor, model, index):
        if index.column() == Column.artist:
            index = editor.currentIndex()
            if index.isValid():
                artist = index.data(Qt.UserRole)
                self.view.show_artist_needed.emit(artist)
        super().setModelData(editor, model, index)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        """set proper width for each column

        HELP: If we do not set width here, the column width
        can be uncertain. I don't know why this would happen,
        since we have set width for the header.
        """
        widths = (0.05, 0.1, 0.25, 0.1, 0.2, 0.3)
        width = self.parent().width()
        w = int(width * widths[index.column()])
        h = option.rect.height()
        return QSize(w, h)

    def editorEvent(self, event, model, option, index):
        super().editorEvent(event, model, option, index)
        return False

    def updateEditorGeometry(self, editor, option, index):
        if index.column() != Column.artist:
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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        # self.verticalHeader().setDefaultSectionSize(40)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        if index.column() == Column.song:
            song = index.data(Qt.UserRole)
            self.play_song_needed.emit(song)
        elif index.column() == Column.artist:
            song = index.data(Qt.UserRole)
            artists = song.artists
            if artists is not None:
                if len(artists) > 1:
                    self.edit(index)
                else:
                    self.show_artist_needed.emit(artists[0])
        elif index.column() == Column.album:
            song = index.data(Qt.UserRole)
            if song.album:
                self.show_album_needed.emit(song.album)
        # FIXME: 在点击之后，音乐数据可能会有更新，理应触发界面更新
        # 测试 dataChanged 似乎不能按照预期工作
        model = self.model()
        topleft = model.createIndex(index.row(), 0)
        bottomright = model.createIndex(index.row(), 4)
        model.dataChanged.emit(topleft, bottomright, [])

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
            if text.lower() not in song.title_display.lower()\
                    and text not in song.album_name_display.lower()\
                    and text not in song.artists_name_display.lower():
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
