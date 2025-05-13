import logging

from enum import IntEnum, Enum
from functools import partial

from PyQt5.QtCore import (
    pyqtSignal, Qt, QVariant, QEvent,
    QAbstractTableModel, QAbstractListModel, QModelIndex,
    QSize, QRect, QPoint, QPointF, QSortFilterProxyModel,
)
from PyQt5.QtGui import QPainter, QPalette, QMouseEvent, QPolygonF
from PyQt5.QtWidgets import (
    QAction, QFrame, QHBoxLayout, QAbstractItemView, QHeaderView,
    QPushButton, QTableView, QWidget, QMenu, QListView,
    QStyle, QSizePolicy, QStyledItemDelegate
)

from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from feeluown.library import ModelState, ModelFlags, MediaFlags

from feeluown.gui.mimedata import ModelMimeData
from feeluown.gui.helpers import (
    ItemViewNoScrollMixin, ReaderFetchMoreMixin, painter_save
)


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
        # Note(cosven): On macOS, 36px is available to show three number.
        # On KDE, even if we set the width to 10px, it does not ellipse the text.
        # In conclusion, I think 36px is good for macOS and KDE.
        width_index = 36
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
            # Note(cosven): Generally, the duration text is about 5 char, like 00:00.
            # On macOS with default font, I found the width of such text is about 55px.
            # The songs table width is about 600px, so set duration ratio to 0.1.
            Column.duration: 0.1,
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
                        parent = self.parent()
                        assert isinstance(parent, SongListView)
                        parent.play_song_needed.emit(index.data(Qt.UserRole))
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
        super().__init__(parent=parent, **kwargs)

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
        no_item_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() in (Column.index, Column.source, Column.duration):
            return no_item_flags

        # Default flags.
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled
        song = index.data(Qt.UserRole)
        # If song's state is `not_exists` or `cant_upgrade`, the album and
        # artist columns are disabled.
        incomplete = False
        if ModelState(song.state) in (ModelState.not_exists, ModelState.cant_upgrade):
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
                parent = self.parent()
                assert isinstance(parent, QWidget)
                w = self.columns_config.get_width(section, parent.width())
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
               (Column.song, Column.artist, Column.album, Column.duration):
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
        # When the selection behaviour is set to QAbstractItemView.SelectRows,
        # len(indexes) is equal to length of items which have ItemIsDragEnabled flag.
        indexes = list(indexes)  # Make typing checkers happy.
        if len(indexes) > 1:
            # UserRole data of all indexes should be the same,
            # so just use the a random one.
            index = indexes[0]
            song = index.data(Qt.UserRole)
            return ModelMimeData(song)


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
    def __init__(self, app, parent):
        super().__init__(parent)
        self._app = app
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
                song = future.result()
                artists = song.artists
            except:  # noqa
                logger.exception('get song.artists failed')
            else:
                model = ArtistsModel(artists)
                editor.setModel(model)
                editor.setCurrentIndex(QModelIndex())

        if index.column() == Column.artist:
            song = index.data(role=Qt.UserRole)
            future = aio.run_fn(self._app.library.song_upgrade, song)
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

        if index.column() == Column.song:
            self.paint_vip_tag(painter, option, index)

        # Draw play button on Column.index when the row is hovered.
        if hovered and index.column() == Column.index:
            painter.save()
            # Override the content drawed by super().paint.
            painter.setPen(Qt.NoPen)
            # HELP(cosven): when an item was hovered, super().paint may draw
            # a semi-transparent rect over the item or draw a different color
            # for the text. The rect/text color may not be in the palette.
            # I checked the qt source code, and I think this behaviour is
            # platform indenpent.It is drawed by something like KDE, kvantum.
            # We have no way to draw a similar look (or please help find a way).
            if index.row() % 2 == 0:
                painter.setBrush(option.palette.color(QPalette.Base))
            else:
                painter.setBrush(option.palette.color(QPalette.AlternateBase))
            painter.drawRect(option.rect)
            # Draw play button.
            painter.setBrush(option.palette.color(QPalette.Text))
            triangle_edge = 12
            triangle_height = 10
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

        # Since the selection behaviour is SelectRows, so draw the mask over the row.
        if hovered:
            painter.save()
            mask_color = option.palette.color(QPalette.Active, QPalette.Text)
            mask_color.setAlpha(20)
            painter.setPen(Qt.NoPen)
            painter.setBrush(mask_color)
            painter.drawRect(option.rect)
            painter.restore()

    def paint_vip_tag(self, painter, option, index):
        song = index.data(Qt.UserRole)
        if (ModelFlags.normal in ModelFlags(song.meta.flags) and
                MediaFlags.vip in MediaFlags(song.media_flags)):
            with painter_save(painter):
                fm = option.fontMetrics
                title = index.data(Qt.DisplayRole)
                title_rect = fm.boundingRect(title)
                if title_rect.width() < option.rect.width():
                    # Tested on (KDE and macOS):
                    #   when font size is 7px, text width~>16 & height~>10
                    font = option.font
                    font.setPixelSize(7)
                    painter.setFont(font)
                    text_width, text_height = 16, 10
                    y = option.rect.y() + (option.rect.height() - text_height) // 2
                    # NOTE(cosven): On macOS, the acture width of text is large than
                    # title_rect.width(), which is also true on KDE. This is decided
                    # by QStyle. +10px works well on macOS, and it also works well
                    # on KDE (actually, from local test, 7px is enough for KDE).
                    x = option.rect.x() + title_rect.width() + 10
                    text_rect = QRect(x, y, text_width, text_height)
                    painter.drawRoundedRect(text_rect, 3, 3)
                    painter.drawText(text_rect, Qt.AlignCenter, 'VIP')

    def sizeHint(self, option, index):
        """set proper width for each column

        HELP: If we do not set width here, the column width
        can be uncertain. I don't know why this would happen,
        since we have set width for the header.
        """
        if index.isValid() and self.parent() is not None:
            # The way getting the sourceModel seems a little strange.
            parent = self.parent()
            assert isinstance(parent, QWidget)
            w = index.model().sourceModel().columns_config.get_width(
                index.column(), parent.width())
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
                    parent = self.parent()
                    assert isinstance(parent, SongsTableView)
                    parent.play_song_needed.emit(index.data(Qt.UserRole))
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

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self._app = app

        # override ItemViewNoScrollMixin variables
        self._least_row_count = 6

        # slot functions
        self.remove_song_func = None  # fn(song)

        self.delegate = SongsTableDelegate(app, self)
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
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Note that the selection behavior affects drop behavior.
        # You may need to to change the Model.flags and mimeData methods
        # if you want to change this behavior.
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

        model = self.model()
        assert isinstance(model, SongFilterProxyModel)
        source = model.sourceModel()
        assert isinstance(source, SongsTableModel)
        source.update_columns_config(columns_config)

        for i in range(0, model.columnCount()):
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
        remove_song_action = QAction('移除歌曲', menu)
        remove_song_action.triggered.connect(
            lambda: self._remove_by_indexes(indexes))
        menu.addSeparator()
        menu.addAction(remove_song_action)
        if self.remove_song_func is None:
            remove_song_action.setDisabled(True)

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
            assert callable(self.remove_song_func)
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
