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
from typing import TypeVar, Optional, List, cast

from PyQt5.QtCore import (
    QAbstractListModel, QModelIndex, Qt,
    QRectF, QRect, QSize, QSortFilterProxyModel
)
from PyQt5.QtGui import (
    QImage, QColor,
    QBrush, QPainter, QTextOption, QFontMetrics, QPalette
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate, QListView, QFrame,
)

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.models.uri import reverse
from feeluown.gui.helpers import (
    ItemViewNoScrollMixin, resize_font, ReaderFetchMoreMixin,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


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


class ImgListModel(QAbstractListModel, ReaderFetchMoreMixin[T]):
    def __init__(self, reader, fetch_image, source_name_map=None, parent=None):
        """

        :param reader: objects in reader should have `name` property
        :param fetch_image: func(item, cb, uid)
        :type reader: Iterable
        """
        super().__init__(parent)

        self.reader = self._reader = wrap(reader)
        self._fetch_more_step = 10
        self._items: List[T] = []
        self._is_fetching = False

        self.source_name_map = source_name_map or {}
        self.fetch_image = fetch_image
        self.colors = []
        self.images = {}  # {uri: QImage}

    def rowCount(self, _=QModelIndex()):
        return len(self._items)

    def _fetch_more_cb(self, items: Optional[List[T]]):
        self._is_fetching = False
        # None means an error occured.
        if items is None:
            return
        if items is not None and not items:
            self.no_more_item.emit()
            return
        items_len = len(items)
        colors = [random.choice(list(COLORS.values())) for _ in range(0, items_len)]
        self.colors.extend(colors)
        self.on_items_fetched(items)
        for item in items:
            aio.create_task(self.fetch_image(item, self._fetch_image_callback(item)))

    def _fetch_image_callback(self, item):
        def cb(content):
            uri = reverse(item)
            if content is None:
                self.images[uri] = None
                return

            img = QImage()
            img.loadFromData(content)
            self.images[uri] = img
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
            image = self.images.get(uri)
            if image is not None:
                return image
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

        self.view = parent
        # TODO: move as_circle/w_h_ratio attribute to view
        self.as_circle = True
        self.w_h_ratio = 1.0

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        text_rect_height = 30
        img_text_height = self.view.img_text_height
        source_rect_height = img_text_height - text_rect_height
        text_y = rect.y() + rect.height() - img_text_height
        cover_height = rect.height() - img_text_height
        cover_width = rect.width()
        text_rect = QRectF(rect.x(), text_y, rect.width(), text_rect_height)
        whats_this_rect = QRectF(
            rect.x(), text_y + text_rect_height - 5,
            rect.width(), source_rect_height + 5
        )
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
        painter.translate(rect.x(), rect.y())
        if isinstance(obj, QColor):
            color = obj
            brush = QBrush(color)
            painter.setBrush(brush)
        else:
            if obj.height() < obj.width():
                img = obj.scaledToHeight(cover_height, Qt.SmoothTransformation)
            else:
                img = obj.scaledToWidth(cover_width, Qt.SmoothTransformation)
            brush = QBrush(img)
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
        elided_name = fm.elidedText(name, Qt.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect, elided_name, option)
        painter.restore()

        # Draw WhatsThis.
        whats_this = index.data(Qt.WhatsThisRole)
        painter.save()
        pen = painter.pen()
        font = painter.font()
        resize_font(font, -2)
        painter.setFont(font)
        pen.setColor(non_text_color)
        painter.setPen(non_text_color)
        painter.drawText(whats_this_rect, whats_this, source_option)
        painter.restore()

    def sizeHint(self, option, index):
        width = self.view.img_sizehint()[0]
        if index.isValid():
            return QSize(width, int(width / self.w_h_ratio) + self.view.img_text_height)
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
        source_model = cast(ImgListModel, self.sourceModel())
        index = source_model.index(source_row, parent=source_parent)
        artist = index.data(Qt.UserRole)
        if self.text:
            accepted = self.text.lower() in artist.name_display.lower()
        return accepted


class ImgListView(ItemViewNoScrollMixin, QListView):
    """
    .. versionadded:: 3.7.7
       The *img_min_width*, *img_spacing*, *img_text_height* parameter were added.
    """
    def __init__(self, parent=None,
                 img_min_width=150, img_spacing=20, img_text_height=40,
                 **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.img_min_width = img_min_width
        self.img_spacing = img_spacing
        self.img_text_height = img_text_height

        # override ItemViewNoScrollMixin variables
        self._least_row_count = 1
        self._row_height = img_min_width + img_spacing + img_text_height

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setSpacing(self.img_spacing)
        self.initialize()

    def resizeEvent(self, e):
        super().resizeEvent(e)

        if self._no_scroll_v is True:
            self._row_height = self.img_sizehint()[1] + self.img_spacing
            self.adjust_height()

    def img_sizehint(self) -> tuple:
        """

        .. versionadded:: 3.7.7
        """
        # HELP: listview needs about 20 spacing left on macOS
        width = self.width() - 20

        img_spacing = self.img_spacing
        img_min_width = self.img_min_width
        img_text_height = self.img_text_height

        # according to our algorithm, when the widget width is:
        #   2(img_min_width + img_spacing) + img_spacing - 1,
        # the cover width can take the maximum width, it will be:
        #   CoverMaxWidth = 2 * img_min_width + img_spacing - 1

        # calculate max column count
        count = (width - img_spacing) // (img_min_width + img_spacing)
        count = max(count, 1)
        img_height = img_width = (width - ((count + 1) * img_spacing)) // count
        img_height = img_height + img_text_height
        return img_width, img_height
