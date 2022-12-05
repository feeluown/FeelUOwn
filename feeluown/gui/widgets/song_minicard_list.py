import logging
import random

from PyQt5.QtCore import (
    pyqtSignal, Qt, QEvent,
    QAbstractListModel, QModelIndex,
    QSize, QRect, QPoint, QRectF
)
from PyQt5.QtGui import (
    QPainter, QMouseEvent, QPixmap, QImage, QColor, QPalette, QBrush,
    QFontMetrics, QTextOption,
)
from PyQt5.QtWidgets import (
    QFrame, QListView, QStyle, QSizePolicy, QStyledItemDelegate
)

from feeluown.utils import aio
from feeluown.models.uri import reverse
from feeluown.gui.helpers import (
    ItemViewNoScrollMixin, ReaderFetchMoreMixin, fetch_cover_wrapper,
    resize_font
)


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
Fetching = object()


class SongMiniCardListModel(QAbstractListModel, ReaderFetchMoreMixin):
    def __init__(self, reader, fetch_image, parent=None):
        super().__init__(parent)

        self._reader = reader
        self._fetch_more_step = 10
        self._items = []
        self._is_fetching = False

        self.fetch_image = fetch_image
        self.colors = []
        self.pixmaps = {}  # {uri: pixmap}

    def rowCount(self, _=QModelIndex()):
        return len(self._items)

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def _fetch_more_cb(self, items):
        self._is_fetching = False
        if items is not None and not items:
            self.no_more_item.emit()
            return
        items_len = len(items)
        colors = [random.choice(list(COLORS.values())) for _ in range(0, items_len)]
        self.colors.extend(colors)
        self.on_items_fetched(items)

    def _fetch_image_callback(self, item):
        # TODO: duplicate code with ImgListModel
        def cb(content):
            uri = reverse(item)
            if content is None:
                self.pixmaps[uri] = None
                return

            img = QImage()
            img.loadFromData(content)
            pixmap = QPixmap(img)
            self.pixmaps[uri] = pixmap
            row = self._items.index(item)
            top_left = self.createIndex(row, 0)
            bottom_right = self.createIndex(row, 0)
            self.dataChanged.emit(top_left, bottom_right)
        return cb

    def get_pixmap_unblocking(self, song):
        """
        :return: None means the song has no pixmap or the pixmap is currently not feched.
        """
        uri = reverse(song)
        if uri in self.pixmaps:
            pixmap = self.pixmaps[uri]
            if pixmap is Fetching:
                return None
            return pixmap
        aio.run_afn(self.fetch_image, song, self._fetch_image_callback(song))
        self.pixmaps[uri] = Fetching

    def data(self, index, role=Qt.DisplayRole):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None
        item = self._items[offset]
        if role == Qt.DisplayRole:
            return self._items[offset].title_display
        elif role == Qt.UserRole:
            song = self._items[offset]
            pixmap = self.get_pixmap_unblocking(song)
            if pixmap is not None:
                return (song, pixmap)
            color_str = self.colors[offset]
            color = QColor(color_str)
            color.setAlphaF(0.8)
            return (song, color)
        return None


class SongMiniCardListDelegate(QStyledItemDelegate):
    def __init__(
        self,
        view,
        card_min_width=200,
        card_height=40,
        card_h_spacing=20,
        card_v_spacing=6,
        card_left_padding=3,
    ):
        super().__init__(parent=view)

        self.view = view
        self.card_min_width = card_min_width
        self.card_height = card_height
        self.card_h_spacing = card_h_spacing
        self.card_v_spacing = card_v_spacing
        self.card_left_padding = card_left_padding

    def card_sizehint(self) -> tuple:
        # HELP: listview needs about 20 spacing left on macOS
        width = max(self.view.width() - 20, self.card_min_width)

        # according to our algorithm, when the widget width is:
        #   2(card_min_width + card_h_spacing) + card_h_spacing - 1,
        # the card width can take the maximum width, it will be:
        #   CardMaxWidth = 2 * card_min_width + card_h_spacing - 1

        # calculate max column count
        count = (width - self.card_h_spacing) // (self.card_min_width + self.card_h_spacing)
        count = max(count, 1)
        card_width = (width - ((count + 1) * self.card_h_spacing)) // count
        card_height = self.card_height + self.card_v_spacing
        return card_width, card_height

    def paint(self, painter, option, index):
        card_v_spacing = self.card_v_spacing
        card_height = self.card_height
        card_left_padding = self.card_left_padding

        rect = option.rect
        cover_height = card_height
        cover_width = cover_height
        song, obj = index.data(Qt.UserRole)
        if obj is None:
            return

        if option.state & QStyle.State_MouseOver:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(option.palette.color(QPalette.Window))
            painter.drawRoundedRect(rect, 3, 3)
            painter.restore()

        painter.save()
        painter.translate(card_left_padding, 0)
        self.paint_pixmap(painter, option, obj, cover_width, cover_height, card_v_spacing)

        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(100)

        # Draw title
        painter.save()
        text_width = option.rect.width() - cover_width - 5
        text_x = rect.topRight().x() - text_width
        text_height = self.card_height // 2
        painter.translate(text_x, rect.y() + card_v_spacing // 2)
        text_rect = QRectF(0, 0, text_width, text_height)
        fm = QFontMetrics(painter.font())
        title = index.data(Qt.DisplayRole)
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elided_title = fm.elidedText(title, Qt.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect, elided_title, text_option)

        # Draw artists_name * album
        painter.translate(0, text_height)
        text_rect = QRectF(0, 0, text_width, text_height)
        fm = QFontMetrics(painter.font())
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text = f'{song.artists_name_display} • {song.album_name_display}'
        elided_title = fm.elidedText(text, Qt.ElideRight, int(text_rect.width()))
        pen = painter.pen()
        font = painter.font()
        resize_font(font, -1)
        painter.setFont(font)
        pen.setColor(non_text_color)
        painter.setPen(non_text_color)
        painter.drawText(text_rect, elided_title, text_option)
        painter.restore()
        painter.restore()

    def paint_pixmap(self, painter, option, decoration, width, height, v_spacing):
        rect = option.rect
        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(100)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(rect.x(), rect.y() + v_spacing // 2)
        pen = painter.pen()
        pen.setColor(non_text_color)
        painter.setPen(pen)
        if isinstance(decoration, QColor):
            color = decoration
            brush = QBrush(color)
            painter.setBrush(brush)
        else:
            if decoration.height() < decoration.width():
                pixmap = decoration.scaledToHeight(height, Qt.SmoothTransformation)
            else:
                pixmap = decoration.scaledToWidth(width, Qt.SmoothTransformation)
            brush = QBrush(pixmap)
            painter.setBrush(brush)
        border_radius = 3
        cover_rect = QRect(0, 0, width, height)
        painter.drawRoundedRect(cover_rect, border_radius, border_radius)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.isValid():
            return QSize(*self.card_sizehint())
        return size



class SongMiniCardListView(ItemViewNoScrollMixin, QListView):

    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        QListView.__init__(self, parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.initialize()

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        self.play_song_needed.emit(index.data(Qt.UserRole)[0])
