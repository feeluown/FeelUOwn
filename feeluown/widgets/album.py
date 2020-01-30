"""

AlbumsTable model-view delegate

- AlbumsTableDelegate
- AlbumsTableView
- AlbumsTableModel

By default, we think the proper width of a album cover is about 160px,
the margin between two cover should be about 20px. When the view is
resized, the cover width and the margin should make a few adjustment.
"""
# pylint: disable=unused-argument
import itertools
import logging
import random

from PyQt5.QtCore import (
    pyqtSignal, QAbstractListModel, QModelIndex, QRectF,
    QRect, QSortFilterProxyModel, QSize, Qt,
)
from PyQt5.QtGui import (
    QBrush, QColor, QImage, QPainter, QPixmap, QTextOption,
    QFontMetrics, QPalette
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate, QListView, QFrame,
)

from fuocore import aio
from fuocore.excs import ProviderIOError
from fuocore.models import GeneratorProxy, AlbumType
from fuocore.models.uri import reverse

from feeluown.helpers import ItemViewNoScrollMixin

logger = logging.getLogger(__name__)


COLORS = {
    'yellow':    '#b58900',
    'orange':    '#cb4b16',
    'red':       '#dc322f',
    'magenta':   '#d33682',
    'violet':    '#6c71c4',
    'blue':      '#268bd2',
    'cyan':      '#2aa198',
    'green':     '#859900',
}

CoverMinWidth = 150
CoverSpacing = 20
TextHeight = 30


def calc_cover_width(width):
    """calculate propert cover width by width width

    according to our algorithm, when the widget width is:
      2(CoverMinWidth + CoverSpacing) + CoverSpacing - 1,
    the cover width can take the maximum width, it will be:
      CoverMaxWidth = 2 * CoverMinWidth + CoverSpacing - 1
    """
    # HELP: listview needs about 20 spacing left on macOS
    width = width - 20
    # calculate max column count
    count = (width - CoverSpacing) // (CoverMinWidth + CoverSpacing)
    cover_width = (width - ((count + 1) * CoverSpacing)) // count
    return cover_width


def calc_album_size(view_width):
    width = cover_height = calc_cover_width(view_width)
    height = cover_height + TextHeight
    return width, height


class AlbumListModel(QAbstractListModel):
    def __init__(self, albums_g, fetch_image, parent=None):
        """
        :param albums_g: :class:`fuocore.models.GeneratorProxy:
        """
        super().__init__(parent)

        self.albums_g = GeneratorProxy.wrap(albums_g)
        self.fetch_image = fetch_image
        # false: no more, true: maybe more
        self._maybe_has_more = True
        self.albums = []
        self.colors = []
        self.pixmaps = {}  # {uri: QPixmap}

    def rowCount(self, parent=QModelIndex()):
        return len(self.albums)

    def canFetchMore(self, _=QModelIndex()):
        count, offset = self.albums_g.count, self.albums_g.offset
        if count is not None:
            return count > offset
        return self._maybe_has_more

    def fetchMore(self, _=QModelIndex()):
        expect_len = 10
        try:
            albums = list(itertools.islice(self.albums_g, expect_len))
        except ProviderIOError:
            logger.exception('fetch more albums failed')
            return

        acture_len = len(albums)
        colors = [random.choice(list(COLORS.values()))
                  for _ in range(0, acture_len)]
        if acture_len < expect_len:
            self._maybe_has_more = False
        begin = len(self.albums)
        self.beginInsertRows(QModelIndex(), begin, begin + acture_len - 1)
        self.albums.extend(albums)
        self.colors.extend(colors)
        self.endInsertRows()

        for album in albums:
            aio.create_task(self.fetch_image(
                album,
                self._fetch_image_callback(album),
                uid=reverse(album) + '/cover'))

    def _fetch_image_callback(self, album):
        def cb(content):
            img = QImage()
            img.loadFromData(content)
            pixmap = QPixmap(img)
            uri = reverse(album)
            self.pixmaps[uri] = pixmap
            row = self.albums.index(album)
            top_left = self.createIndex(row, 0)
            bottom_right = self.createIndex(row, 0)
            self.dataChanged.emit(top_left, bottom_right)
        return cb

    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self.albums):
            return None
        album = self.albums[offset]
        if role == Qt.DecorationRole:
            uri = reverse(album)
            pixmap = self.pixmaps.get(uri)
            if pixmap is not None:
                return pixmap
            color_str = self.colors[offset]
            color = QColor(color_str)
            color.setAlphaF(0.8)
            return color
        elif role == Qt.DisplayRole:
            return album.name_display
        elif role == Qt.UserRole:
            return album
        return None


class AlbumFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None, types=None):
        super().__init__(parent)

        self.text = ''
        self.types = types

    def filter_by_types(self, types):
        # if tyeps is a empty list or None, we show all albums
        if not types:
            types = None
        self.types = types
        self.invalidateFilter()

    def filter_by_text(self, text):
        self.text = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        accepted = True
        source_model = self.sourceModel()
        index = source_model.index(source_row, parent=source_parent)
        album = index.data(Qt.UserRole)
        if accepted and self.types:
            accepted = AlbumType(album.type) in self.types
        if accepted and self.text:
            accepted = self.text.lower() in album.name_display.lower()
        return accepted


class AlbumListDelegate(QAbstractItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        text_rect_height = TextHeight
        cover_spacing = 0
        text_y = rect.y() + rect.height() - text_rect_height
        cover_height = rect.height() - text_rect_height
        cover_width = rect.width() - cover_spacing
        cover_x = rect.x() + cover_spacing // 2
        cover_y = rect.y()
        text_rect = QRectF(rect.x(), text_y, rect.width(), text_rect_height)
        obj = index.data(Qt.DecorationRole)
        if obj is None:
            painter.restore()
            return

        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(100)
        painter.save()
        pen = painter.pen()
        pen.setColor(non_text_color)
        painter.setPen(pen)
        painter.translate(cover_x, cover_y)
        cover_rect = QRect(0, 0, cover_width, cover_height)
        if isinstance(obj, QColor):
            color = obj
            brush = QBrush(color)
            painter.setBrush(brush)
        else:
            pixmap = obj.scaledToWidth(cover_width, Qt.SmoothTransformation)
            brush = QBrush(pixmap)
            painter.setBrush(brush)
        painter.drawRoundedRect(cover_rect, 3, 3)
        painter.restore()
        option = QTextOption()
        option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        album_name = index.data(Qt.DisplayRole)
        fm = QFontMetrics(painter.font())
        elided_album_name = fm.elidedText(album_name, Qt.ElideRight, text_rect.width())
        painter.drawText(text_rect, elided_album_name, option)
        painter.restore()

    def sizeHint(self, option, index):
        width = calc_cover_width(self.parent().width())
        if index.isValid():
            return QSize(
                width,
                width + TextHeight)
        return super().sizeHint(option, index)


class AlbumListView(ItemViewNoScrollMixin, QListView):

    show_album_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__()
        QListView.__init__(self, parent=parent)

        # override ItemViewNoScrollMixin variables
        self._least_row_count = 1
        self._row_height = CoverMinWidth + CoverSpacing + TextHeight

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setFrameShape(QFrame.NoFrame)

        delegate = AlbumListDelegate(self)
        self.setItemDelegate(delegate)
        self.setSpacing(CoverSpacing)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        album = index.data(Qt.UserRole)
        self.show_album_needed.emit(album)

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self._row_height = calc_album_size(self.width())[1] + CoverSpacing
        self.adjust_height()
