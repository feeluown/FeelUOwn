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

from feeluown.helpers import action_log, ActionError


logger = logging.getLogger(__name__)


class PlaylistsModel(QAbstractListModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._playlists = []
        self._fav_playlists = []

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
        playlists.extend(playlist)
        self.endInsertRows()

    def rowCount(self, _):
        return len(self._playlists) + len(self._fav_playlists)

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.row() < len(self._playlists):
            flags |= Qt.ItemIsDropEnabled
        return flags

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # XXX: 实际不产生任何效果
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return '播放列表'
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        # 新创建的 playlists 中的元素是引用
        playlists = self._playlists + self._fav_playlists
        if row >= len(playlists) or row < 0:
            return QVariant()

        playlist = playlists[row]
        if role == Qt.DisplayRole:
            if row < len(self._playlists):
                flag = '♬ '
            else:
                flag = '★ '
            return flag + playlist.name
        elif role == Qt.UserRole:
            return playlist
        return QVariant()


class PlaylistsView(QListView):

    show_playlist = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

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
                text = '⇵'
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
