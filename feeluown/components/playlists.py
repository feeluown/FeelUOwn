import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    Qt,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    QTimer,
    QVariant,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QFontMetrics,
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

from .textlist import TextlistModel, TextlistView

from feeluown.helpers import action_log, ActionError


logger = logging.getLogger(__name__)


class PlaylistsModel(TextlistModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._playlists = []
        self._fav_playlists = []

    @property
    def items(self):
        return self._playlists + self._fav_playlists

    def add(self, playlist, is_fav=False):
        if is_fav:
            start = len(self._playlists) + len(self._fav_playlists)
            playlists = self._fav_playlists
        else:
            start = len(self._playlists)
            playlists = self._playlists

        if isinstance(playlist, list):
            _playlists = playlist
        else:
            _playlists = [playlist]
        end = start + len(_playlists)
        self.beginInsertRows(QModelIndex(), start, end)
        playlists.extend(_playlists)
        self.endInsertRows()

    def clear(self):
        total_length = len(self.items)
        self.beginRemoveRows(QModelIndex(), 0, total_length - 1)
        self._playlists = []
        self._fav_playlists = []
        self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.row() < len(self._playlists):
            flags |= Qt.ItemIsDropEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        playlist = self.items[row]
        if role == Qt.DisplayRole:
            if row < len(self._playlists):
                flag = '♬ '
            else:
                flag = '★ '
            return flag + playlist.name
        return super().data(index, role)


class PlaylistsView(TextlistView):
    """歌单列表视图

    该视图会显示所有的元素，理论上不会有滚动条，也不接受滚动事件
    """
    show_playlist = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.clicked.connect(self._on_clicked)

        self._result_timer = QTimer(self)
        self._result_timer.timeout.connect(self.__on_timeout)
        self._results = {}  # {row: [index, True]}

    def _on_clicked(self, index):
        playlist = index.data(role=Qt.UserRole)
        self.show_playlist.emit(playlist)

    def __on_timeout(self):
        self._result_timer.stop()
        self._results.clear()
        self.viewport().update()

    def dropEvent(self, e):
        mimedata = e.mimeData()
        if mimedata.hasFormat('fuo-model/x-song'):
            song = mimedata.model
            index = self.indexAt(e.pos())
            playlist = index.data(Qt.UserRole)
            if song.source != playlist.source:
                e.ignore()
                return
            with action_log('Add {} to {}'.format(song, playlist)):
                self._results[index.row] = (index, None)
                self.viewport().update()
                is_success = playlist.add(song.identifier)
                self._results[index.row] = (index, is_success)
                self.viewport().update()
                self._result_timer.start(2000)
                if not is_success:
                    raise ActionError
            e.accept()
        else:
            e.ignore()

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self._results:
            return
        painter = QPainter(self.viewport())
        option = self.viewOptions()
        painter.setRenderHint(QPainter.Antialiasing)
        fm = QFontMetrics(option.font)
        for row, result in self._results.items():
            index, state = result
            rect = self.rectForIndex(index)
            if state is None:
                text = '😶'
            elif state is True:
                text = '👋'
            else:
                text = '🙁'
            x = rect.width() - 20 + rect.x()
            # 让字垂直居中
            y = (rect.height() + fm.ascent() - fm.descent()) / 2 + rect.y()
            topleft = QPoint(x, y)
            painter.drawText(topleft, text)

    def dragEnterEvent(self, e):
        e.accept()

    def dragMoveEvent(self, e):
        index = self.indexAt(e.pos())
        if index.flags() & Qt.ItemIsDropEnabled:
            e.accept()
        else:
            e.ignore()
