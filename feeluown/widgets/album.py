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
import random

from PyQt5.QtCore import (
    pyqtSignal,
    QAbstractListModel,
    QModelIndex,
    QRectF,
    QSize,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QImage,
    QPainter,
    QPixmap,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QListView,
)

from fuocore.models import GeneratorProxy
from fuocore.protocol import get_url


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

CoverMinWidth = 130
CoverSpacing = 15
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
        albums = list(itertools.islice(self.albums_g, expect_len))
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

        # FIXME: since album.cover may trigger web request,
        # this may block the UI
        for album in albums:
            cover = album.cover
            self.fetch_image(cover,
                             self._fetch_image_callback(album),
                             uid=get_url(album) + '/cover')

    def _fetch_image_callback(self, album):
        def cb(future):
            if not future.done():
                return
            content = future.result()
            img = QImage()
            img.loadFromData(content)
            pixmap = QPixmap(img)
            uri = get_url(album)
            self.pixmaps[uri] = pixmap
        return cb

    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self.albums):
            return None
        album = self.albums[offset]
        if role == Qt.DecorationRole:
            uri = get_url(album)
            pixmap = self.pixmaps.get(uri)
            if pixmap is not None:
                return pixmap
            color_str = self.colors[offset]
            color = QColor(color_str)
            color.setAlphaF(0.8)
            return color
        elif role == Qt.DisplayRole:
            return album.name
        elif role == Qt.UserRole:
            return album
        return None


class AlbumListDelegate(QAbstractItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        text_rect_height = 30
        cover_spacing = 0
        text_y = rect.y() + rect.height() - text_rect_height
        cover_height = rect.height() - text_rect_height
        cover_width = rect.width() - cover_spacing
        cover_x = rect.x() + cover_spacing // 2
        cover_y = rect.y()
        text_rect = QRectF(rect.x(), text_y + 5, rect.width(), text_rect_height)
        obj = index.data(Qt.DecorationRole)
        if obj is None:
            painter.restore()
            return
        elif isinstance(obj, QColor):
            color = obj
            brush = QBrush(color)
            painter.setBrush(brush)
            painter.drawRect(cover_x, cover_y, cover_width, cover_height)
        else:
            pixmap = obj.scaledToWidth(cover_width, Qt.SmoothTransformation)
            painter.drawPixmap(cover_x, cover_y, pixmap)
        option = QTextOption()
        option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        album_name = index.data(Qt.DisplayRole)
        painter.drawText(text_rect, album_name, option)
        painter.restore()

    def sizeHint(self, option, index):
        width = calc_cover_width(self.parent().width())
        if index.isValid():
            return QSize(
                width,
                width + TextHeight)
        return super().sizeHint(option, index)


class AlbumListView(QListView):

    show_album_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)

        delegate = AlbumListDelegate(self)
        self.setItemDelegate(delegate)
        self.setSpacing(CoverSpacing)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        album = index.data(Qt.UserRole)
        self.show_album_needed.emit(album)
