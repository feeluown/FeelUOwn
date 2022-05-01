import logging

from enum import IntEnum, Enum
from functools import partial

from PyQt5.QtCore import (
    pyqtSignal, Qt, QVariant, QEvent,
    QAbstractTableModel, QAbstractListModel, QModelIndex,
    QSize, QRect, QPoint, QPointF, QSortFilterProxyModel,
)
from PyQt5.QtGui import QPainter, QPalette, QPen, QMouseEvent, QPolygonF
from PyQt5.QtWidgets import (
    QAction, QFrame, QHBoxLayout, QAbstractItemView, QHeaderView,
    QPushButton, QTableView, QWidget, QMenu, QListView,
    QStyle, QSizePolicy, QStyledItemDelegate,
)

from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from feeluown.excs import ProviderIOError
from feeluown.library import ModelState, ModelFlags
from feeluown.models import ModelExistence

from feeluown.gui.mimedata import ModelMimeData
from feeluown.gui.helpers import ItemViewNoScrollMixin, ReaderFetchMoreMixin


logger = logging.getLogger(__name__)


class ColumnsMode(Enum):
    """
    Different mode show different columns.
    """
    normal = 'normal'
    album = 'album'
    artist = 'artist'
    playlist = 'playlist'


class Column(IntEnum):
    index = 0
    song = 1
    source = 5
    duration = 4
    artist = 2
    album = 3


class ColumnsConfig:
    """
    TableView use sizeHint to control the width of each row. In order to make
    size hint taking effects, resizeMode should be se to ResizeToContents.
    """

    def __init__(self, widths):
        self._widths = widths

    def set_width_ratio(self, column, ratio):
        self._widths[column] = ratio

    def get_width(self, column, table_width):
        width_index = 10
        if column == Column.index:
            return width_index
        width = table_width - width_index
        # Column.song is always set to stetch, the column width is decided by
        #   (total_width - other column widths).
        # So the ratio of column.song does not take any effects actually.
        ratio = self._widths[column]
        return int(width * ratio)

    @classmethod
    def default(cls):
        widths = {
            Column.song: 0.4,
            Column.artist: 0.15,
            Column.album: 0.25,
            Column.duration: 0.05,
            Column.source: 0.15,
        }
        return cls(widths=widths)


def get_column_name(column):
    return {
        Column.index: '',
        Column.song: '歌曲标题',
        Column.artist: '歌手',
        Column.album: '专辑',
        Column.duration: '时长',
        Column.source: '来源',
    }[column]


class SongListModel(QAbstractListModel, ReaderFetchMoreMixin):
    def __init__(self, reader, parent=None):
        super().__init__(parent)

        self._reader = reader
        self._fetch_more_step = 10
        self._items = []
        self._is_fetching = False

    def rowCount(self, _=QModelIndex()):
        return len(self._items)

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            return self._items[row].title_display
        elif role == Qt.UserRole:
            return self._items[row]
        return None


class SongListDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent=parent)

        # the rect.x the number text
        self.number_rect_x = 20
        self.play_btn_pressed = False

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        song = index.data(Qt.UserRole)
        top = option.rect.top()
        bottom = option.rect.bottom()
        no_x = self.number_rect_x
        duration_width = 100
        artists_name_width = 150

        # Draw duration ms
        duration_x = option.rect.topRight().x() - duration_width
        duration_rect = QRect(QPoint(duration_x, top), option.rect.bottomRight())
        painter.drawText(duration_rect, Qt.AlignRight | Qt.AlignVCenter,
                         song.duration_ms_display)

        # Draw artists name
        artists_name_x = option.rect.topRight().x() - duration_width - artists_name_width
        artists_name_rect = QRect(QPoint(artists_name_x, top),
                                  QPoint(duration_x, bottom))
        painter.drawText(artists_name_rect, Qt.AlignRight | Qt.AlignVCenter,
                         song.artists_name_display)

        # Draw song number or play_btn when it is hovered
        no_bottom_right = QPoint(no_x, bottom)
        no_rect = QRect(option.rect.topLeft(), no_bottom_right)
        if option.state & QStyle.State_MouseOver:  # type: ignore
            painter.drawText(no_rect, Qt.AlignLeft | Qt.AlignVCenter, '►')
        else:
            painter.drawText(no_rect, Qt.AlignLeft | Qt.AlignVCenter,
                             str(index.row() + 1))

        # Draw title
        title_rect = QRect(QPoint(no_x, top), QPoint(artists_name_x, bottom))
        painter.drawText(title_rect, Qt.AlignVCenter, song.title_display)

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


class SongListView(ItemViewNoScrollMixin, QListView):

    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        QListView.__init__(self, parent)

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


class BaseSongsTableModel(QAbstractTableModel):
    def __init__(self, source_name_map=None, parent=None):
        super().__init__(parent)

        self.columns_config = ColumnsConfig.default()
        self._items = []
        self._source_name_map = source_name_map or {}

    def update_columns_config(self, columns_config):
        """
        :param columns: see `create_columns` result.
        """
        self.columns_config = columns_config

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        while count > 0:
            self._items.pop(row)
            count -= 1
        self.endRemoveRows()
        return True

    def flags(self, index):
        # Qt.NoItemFlags is ItemFlag and we should return ItemFlags
        no_item_flags = Qt.ItemIsSelectable
        if index.column() in (Column.source, Column.index, Column.duration):
            return no_item_flags

        # default flags
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == Column.song:
            flags |= Qt.ItemIsDragEnabled

        song = index.data(Qt.UserRole)
        # If song's state is `not_exists` or `cant_upgrade`, the album and
        # artist columns are disabled.
        incomplete = False
        if ModelFlags.v2 & song.meta.flags:
            if song.state is (ModelState.not_exists, ModelState.cant_upgrade):
                incomplete = True
        else:
            if song and song.exists == ModelExistence.no:
                incomplete = True
        if incomplete:
            if index.column() != Column.song:
                flags = no_item_flags
        else:
            if index.column() == Column.album:
                flags |= Qt.ItemIsDragEnabled
            elif index.column() == Column.artist:
                flags |= Qt.ItemIsEditable

        return flags

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, _=QModelIndex()):
        return 6

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return get_column_name(section)
            elif role == Qt.SizeHintRole and self.parent() is not None:
                # we set height to 25 since the header can be short under macOS.
                # HELP: set height to fixed value manually is not so elegant
                height = 25
                w = self.columns_config.get_width(section, self.parent().width())
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
        if index.row() >= len(self._items) or index.row() < 0:
            return QVariant()

        song = self._items[index.row()]
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            # Only show tooltip for song/artist/album fields.
            if role == Qt.ToolTipRole and index.column() not in \
               (Column.song, Column.artist, Column.album):
                return QVariant()
            if index.column() == Column.index:
                return index.row() + 1
            elif index.column() == Column.source:
                name = source = song.source
                return self._source_name_map.get(source, name).strip()
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
                return Qt.AlignLeft | Qt.AlignBaseline | Qt.AlignVCenter
        elif role == Qt.EditRole:
            return 1
        elif role == Qt.UserRole:
            return song
        return QVariant()

    def mimeData(self, indexes):
        if len(indexes) == 1:
            index = indexes[0]
            model = song = index.data(Qt.UserRole)
            if index.column() == Column.album:
                try:
                    model = song.album
                except (ProviderIOError, Exception):
                    model = None
            return ModelMimeData(model)


class SongsTableModel(BaseSongsTableModel, ReaderFetchMoreMixin):
    def __init__(self, reader, **kwargs):
        """

        :param songs: 歌曲列表
        :param songs_g: 歌曲列表生成器（当歌曲列表生成器不为 None 时，忽略 songs 参数）
        """
        super().__init__(**kwargs)
        self._reader = reader
        self._fetch_more_step = 30
        self._is_fetching = False

    @property
    def reader(self):
        return self._reader


class SongFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None, text=''):
        super().__init__(parent)

        self.text = text

    def filter_by_text(self, text):
        # if text is an empty string or None, we show all songs
        self.text = text or ''
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.text:
            return super().filterAcceptsRow(source_row, source_parent)

        source_model = self.sourceModel()
        index = source_model.index(source_row, Column.song, parent=source_parent)
        song = index.data(Qt.UserRole)
        text = self.text.lower()
        ctx = song.title_display.lower() + \
            song.album_name_display.lower() + \
            song.artists_name_display.lower()
        return text in ctx


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
        self.row_hovered = None  # A valid row_id if hovered.
        self.pressed_cell = None  # (row, column) if pressed.

    def on_row_hovered(self, row):
        self.row_hovered = row

    def createEditor(self, parent, option, index):
        if index.column() == Column.artist:
            editor = ArtistsSelectionView(parent)
            editor.clicked.connect(partial(self.commitData.emit, editor))
            editor.move(parent.mapToGlobal(option.rect.bottomLeft()))
            editor.setFixedWidth(option.rect.width())
            return editor

    def setEditorData(self, editor, index):
        super().setEditorData(editor, index)

        def cb(future):
            try:
                artists = future.result()
            except:  # noqa
                logger.error('song.artists failed')
            else:
                model = ArtistsModel(artists)
                editor.setModel(model)
                editor.setCurrentIndex(QModelIndex())

        if index.column() == Column.artist:
            song = index.data(role=Qt.UserRole)
            future = aio.run_in_executor(None, lambda: song.artists)
            future.add_done_callback(cb)

    def setModelData(self, editor, model, index):
        if index.column() == Column.artist:
            index = editor.currentIndex()
            if index.isValid():
                artist = index.data(Qt.UserRole)
                self.view.show_artist_needed.emit(artist)
        super().setModelData(editor, model, index)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        painter.setRenderHint(QPainter.Antialiasing)
        hovered = index.row() == self.row_hovered

        # Draw play button on Column.index when the row is hovered.
        if hovered and index.column() == Column.index:
            painter.save()
            # Override contents.
            if option.state & QStyle.State_Selected:  # type: ignore
                bgcolor = option.palette.color(QPalette.Active, QPalette.Highlight)
                fgcolor = option.palette.color(QPalette.Active, QPalette.HighlightedText)
            else:
                bgcolor = option.palette.color(QPalette.Active, QPalette.Base)
                fgcolor = option.palette.color(QPalette.Active, QPalette.Text)
            painter.setBrush(bgcolor)
            painter.setPen(Qt.NoPen)
            painter.drawRect(option.rect)
            # Draw play button.
            triangle_edge = 12
            triangle_height = 10
            painter.setBrush(fgcolor)
            # Move the triangle right 2px and it looks better.
            painter.translate(
                2 + option.rect.x() + (option.rect.width() - triangle_height)//2,
                option.rect.y() + (option.rect.height() - triangle_edge)//2
            )
            triangle = QPolygonF([QPointF(0, 0),
                                  QPointF(triangle_height, triangle_edge//2),
                                  QPointF(0, triangle_edge)])
            painter.drawPolygon(triangle)
            painter.restore()

        # Draw a line under each row. If it is hovered, highlight the line.
        painter.save()
        pen = QPen()
        line_color = option.palette.color(QPalette.Active, QPalette.Text)
        line_color.setAlpha(30)
        pen.setColor(line_color)
        painter.setPen(pen)
        bottom_left = option.rect.bottomLeft()
        bottom_right = option.rect.bottomRight()
        if index.model().columnCount() - 1 == index.column():
            bottom_right = QPoint(bottom_right.x(), bottom_right.y())
        if index.column() == 0:
            bottom_left = QPoint(bottom_left.x(), bottom_right.y())
        painter.drawLine(bottom_left, bottom_right)
        painter.restore()

        # Draw the mask over the row.
        if hovered:
            painter.save()
            mask_color = option.palette.color(QPalette.Active, QPalette.Text)
            mask_color.setAlpha(20)
            painter.setPen(Qt.NoPen)
            painter.setBrush(mask_color)
            painter.drawRect(option.rect)
            painter.restore()

    def sizeHint(self, option, index):
        """set proper width for each column

        HELP: If we do not set width here, the column width
        can be uncertain. I don't know why this would happen,
        since we have set width for the header.
        """
        if index.isValid() and self.parent() is not None:
            # The way getting the sourceModel seems a little strange.
            w = index.model().sourceModel().columns_config.get_width(
                index.column(), self.parent().width())
            h = option.rect.height()
            return QSize(w, h)
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        etype = event.type()
        if etype in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            cell = (index.row(), index.column())
            if etype == QEvent.MouseButtonPress:
                self.pressed_cell = cell
            elif etype == QEvent.MouseButtonRelease:
                if cell == self.pressed_cell and cell[1] == Column.index:
                    self.parent().play_song_needed.emit(index.data(Qt.UserRole))
                self.pressed_cell = None

        return super().editorEvent(event, model, option, index)

    def updateEditorGeometry(self, editor, option, index):
        if index.column() != Column.artist:
            super().updateEditorGeometry(editor, option, index)


class SongsTableView(ItemViewNoScrollMixin, QTableView):

    show_artist_needed = pyqtSignal([object])
    show_album_needed = pyqtSignal([object])
    play_song_needed = pyqtSignal([object])

    add_to_playlist_needed = pyqtSignal(list)

    row_hovered = pyqtSignal([object])  # None when not hovered, row id when hovered.

    def __init__(self, parent=None):
        super().__init__(parent)
        QTableView.__init__(self, parent)

        # override ItemViewNoScrollMixin variables
        self._least_row_count = 6
        self._row_height = 40

        # slot functions
        self.remove_song_func = None

        self.delegate = SongsTableDelegate(self)
        self.setItemDelegate(self.delegate)
        self.about_to_show_menu = Signal()
        self._setup_ui()

        self.row_hovered.connect(self.delegate.on_row_hovered)
        self.entered.connect(lambda index: self.row_hovered.emit(index.row()))

    def _setup_ui(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(self._row_height)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)

    def setModel(self, model):
        super().setModel(model)
        self.horizontalHeader().setSectionResizeMode(Column.song, QHeaderView.Stretch)

    def set_columns_mode(self, mode):
        mode = ColumnsMode(mode)
        columns_config = ColumnsConfig.default()
        if mode is ColumnsMode.normal:
            hide_columns = []
        elif mode is ColumnsMode.album:
            hide_columns = [Column.album, Column.source]
            columns_config.set_width_ratio(Column.artist, 0.25)
            columns_config.set_width_ratio(Column.duration, 0.1)
        else:  # artist/playlist mode.
            hide_columns = [Column.source]
            columns_config.set_width_ratio(Column.artist, 0.2)
            columns_config.set_width_ratio(Column.album, 0.3)
        self.model().sourceModel().update_columns_config(columns_config)

        for i in range(0, self.model().columnCount()):
            if i in hide_columns:
                self.hideColumn(i)
            else:
                self.showColumn(i)

    def show_artists_by_index(self, index):
        self.edit(index)

    def contextMenuEvent(self, event):
        indexes = self.selectionModel().selectedIndexes()
        if len(indexes) <= 0:
            return

        menu = QMenu()

        # add to playlist action
        add_to_playlist_action = QAction('添加到播放队列', menu)
        add_to_playlist_action.triggered.connect(lambda: self._add_to_playlist(indexes))
        menu.addAction(add_to_playlist_action)

        # remove song action
        if self.remove_song_func is not None:
            remove_song_action = QAction('移除歌曲', menu)
            remove_song_action.triggered.connect(
                lambda: self._remove_by_indexes(indexes))
            menu.addSeparator()
            menu.addAction(remove_song_action)

        model = self.model()
        models = [model.data(index, Qt.UserRole) for index in indexes]

        def add_action(text, callback):
            action = QAction(text, menu)
            menu.addSeparator()
            menu.addAction(action)
            action.triggered.connect(lambda: callback(models))

        # .. versionadded: 3.7
        #   The context key *models*
        # .. versionadded: 3.7.11
        #   The context key *menu*
        self.about_to_show_menu.emit({'add_action': add_action,
                                      'menu': menu,
                                      'models': models})
        menu.exec(event.globalPos())

    def _add_to_playlist(self, indexes):
        model = self.model()
        songs = []
        for index in indexes:
            song = model.data(index, Qt.UserRole)
            songs.append(song)
        self.add_to_playlist_needed.emit(songs)

    def _remove_by_indexes(self, indexes):
        model = self.model()
        # We don't use set because song may be a not hashable object.
        songs_to_remove = []
        for index in indexes:
            song = model.data(index, Qt.UserRole)
            if song not in songs_to_remove:
                songs_to_remove.append(song)
        for song in songs_to_remove:
            self.remove_song_func(song)

    def viewportEvent(self, event):
        res = super().viewportEvent(event)
        if event.type() == QEvent.Leave:
            self.row_hovered.emit(None)
        return res

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self.indexAt(event.pos()).isValid():
            self.row_hovered.emit(None)
