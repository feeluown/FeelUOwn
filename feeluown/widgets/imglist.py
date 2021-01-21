"""
ImgList model and delegate

- ImgListDelegate
- ImgListModel

By default, we think the proper width of a cover is about 160px,
the margin between two cover should be about 20px. When the view is
resized, the cover width and the margin should make a few adjustment.
"""

# pylint: disable=unused-argument
import logging
import random

from PyQt5.QtCore import (
    QAbstractListModel, QModelIndex, Qt,
    QRectF, QRect, QSize, QSortFilterProxyModel
)
from PyQt5.QtGui import (
    QImage, QPixmap, QColor,
    QBrush, QPainter, QTextOption, QFontMetrics, QPalette
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate, QListView, QFrame,
)

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.models.uri import reverse
from feeluown.gui.helpers import ItemViewNoScrollMixin, resize_font, ReaderFetchMoreMixin

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
TextHeight = 40


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
    count = max(count, 1)
    cover_width = (width - ((count + 1) * CoverSpacing)) // count
    return cover_width


def calc_cover_size(view_width):
    width = cover_height = calc_cover_width(view_width)
    height = cover_height + TextHeight
    return width, height


class ImgListModel(QAbstractListModel, ReaderFetchMoreMixin):
    def __init__(self, reader, fetch_image, source_name_map=None, parent=None):
        """

        :param reader: objects in reader should have `name` property
        :param fetch_image: func(item, cb, uid)
        :type reader: Iterable
        """
        super().__init__(parent)

        self.reader = self._reader = wrap(reader)
        self._fetch_more_step = 10
        self._items = []
        self._is_fetching = False

        self.source_name_map = source_name_map or {}
        self.fetch_image = fetch_image
        self.colors = []
        self.pixmaps = {}  # {uri: QPixmap}

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def _fetch_more_cb(self, items):
        if items is None:
            return
        items_len = len(items)
        colors = [random.choice(list(COLORS.values())) for _ in range(0, items_len)]
        self.colors.extend(colors)
        self.on_items_fetched(items)
        for item in items:
            aio.create_task(self.fetch_image(
                item,
                self._fetch_image_callback(item),
                uid=reverse(item) + '/cover'))

    def _fetch_image_callback(self, item):
        def cb(content):
            img = QImage()
            img.loadFromData(content)
            pixmap = QPixmap(img)
            uri = reverse(item)
            self.pixmaps[uri] = pixmap
            row = self._items.index(item)
            top_left = self.createIndex(row, 0)
            bottom_right = self.createIndex(row, 0)
            self.dataChanged.emit(top_left, bottom_right)
        return cb

    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None
        item = self._items[offset]
        if role == Qt.DecorationRole:
            uri = reverse(item)
            pixmap = self.pixmaps.get(uri)
            if pixmap is not None:
                return pixmap
            color_str = self.colors[offset]
            color = QColor(color_str)
            color.setAlphaF(0.8)
            return color
        elif role == Qt.DisplayRole:
            return item.name_display
        elif role == Qt.UserRole:
            return item
        elif role == Qt.WhatsThisRole:
            return self.source_name_map.get(item.source, item.source)
        return None


class ImgListDelegate(QAbstractItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.as_circle = True
        self.w_h_ratio = 1

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        text_rect_height = 30
        source_rect_height = TextHeight - text_rect_height
        cover_spacing = 0
        text_y = rect.y() + rect.height() - TextHeight
        cover_height = rect.height() - TextHeight
        cover_width = rect.width() - cover_spacing
        cover_x = rect.x() + cover_spacing // 2
        cover_y = rect.y()
        text_rect = QRectF(rect.x(), text_y, rect.width(), text_rect_height)
        source_rect = QRectF(rect.x(), text_y + text_rect_height - 5,
                             rect.width(), source_rect_height + 5)
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
        if isinstance(obj, QColor):
            color = obj
            brush = QBrush(color)
            painter.setBrush(brush)
        else:
            if obj.height() < obj.width():
                pixmap = obj.scaledToHeight(cover_height, Qt.SmoothTransformation)
            else:
                pixmap = obj.scaledToWidth(cover_width, Qt.SmoothTransformation)
            brush = QBrush(pixmap)
            painter.setBrush(brush)
        border_radius = 3
        if self.as_circle:
            border_radius = cover_width // 2
        cover_rect = QRect(0, 0, cover_width, cover_height)
        painter.drawRoundedRect(cover_rect, border_radius, border_radius)
        painter.restore()
        option = QTextOption()
        source_option = QTextOption()
        if self.as_circle:
            option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            source_option.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        else:
            option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            source_option.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        name = index.data(Qt.DisplayRole)
        fm = QFontMetrics(painter.font())
        elided_name = fm.elidedText(name, Qt.ElideRight, text_rect.width())
        source = index.data(Qt.WhatsThisRole)
        painter.drawText(text_rect, elided_name, option)
        painter.restore()
        painter.save()
        pen = painter.pen()
        font = painter.font()
        resize_font(font, -2)
        painter.setFont(font)
        pen.setColor(non_text_color)
        painter.setPen(non_text_color)
        painter.drawText(source_rect, source, source_option)
        painter.restore()

    def sizeHint(self, option, index):
        width = calc_cover_width(self.parent().width())
        if index.isValid():
            return QSize(width, int(width / self.w_h_ratio) + TextHeight)
        return super().sizeHint(option, index)


class ImgFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None, types=None):
        super().__init__(parent)

        self.text = ''

    def filter_by_text(self, text):
        if text == self.text:
            return
        self.text = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        accepted = True
        source_model = self.sourceModel()
        index = source_model.index(source_row, parent=source_parent)
        artist = index.data(Qt.UserRole)
        if self.text:
            accepted = self.text.lower() in artist.name_display.lower()
        return accepted


class ImgListView(ItemViewNoScrollMixin, QListView):

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
        self.setSpacing(CoverSpacing)

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self._row_height = calc_cover_size(self.width())[1] + CoverSpacing
        self.adjust_height()
