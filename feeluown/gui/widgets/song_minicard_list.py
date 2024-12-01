import logging
import random
from typing import TYPE_CHECKING

from PyQt5.QtCore import (
    pyqtSignal, Qt, QSize, QRect, QRectF,
    QAbstractListModel, QModelIndex,
)
from PyQt5.QtGui import (
    QPainter, QPixmap, QImage, QColor, QPalette, QBrush,
    QFontMetrics, QTextOption, QGuiApplication,
)
from PyQt5.QtWidgets import (
    QFrame, QListView, QStyle, QStyledItemDelegate
)

from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.library import reverse
from feeluown.gui.helpers import (
    ItemViewNoScrollMixin, ReaderFetchMoreMixin, resize_font, SOLARIZED_COLORS,
    fetch_cover_wrapper,
)

if TYPE_CHECKING:
    from feeluown.gui import GuiApp


logger = logging.getLogger(__name__)
Fetching = object()


class BaseSongMiniCardListModel(QAbstractListModel):
    def __init__(self, fetch_image, parent=None):
        super().__init__(parent)

        self._items = []
        self.fetch_image = fetch_image
        self.pixmaps = {}  # {uri: (Option<pixmap>, Option<color>)}
        self.rowsAboutToBeRemoved.connect(self.on_rows_about_to_be_removed)

    def rowCount(self, _=QModelIndex()):
        return len(self._items)

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def _fetch_image_callback(self, item):
        # TODO: duplicate code with ImgListModel
        def cb(content):
            uri = reverse(item)
            if content is None and uri in self.pixmaps:
                self.pixmaps[uri] = (self.pixmaps[uri][1], None)
                return

            img = QImage()
            img.loadFromData(content)
            pixmap = QPixmap(img)
            self.pixmaps[uri] = (pixmap, None)
            row = self._items.index(item)
            top_left = self.createIndex(row, 0)
            bottom_right = self.createIndex(row, 0)
            self.dataChanged.emit(top_left, bottom_right)
        return cb

    def get_pixmap_unblocking(self, song):
        """
        return QColor means the song has no pixmap or the pixmap is currently not feched.
        """
        uri = reverse(song)
        if uri in self.pixmaps:
            pixmap, color = self.pixmaps[uri]
            if pixmap is Fetching:
                return color
            return pixmap
        aio.run_afn(self.fetch_image, song, self._fetch_image_callback(song))
        color = QColor(random.choice(list(SOLARIZED_COLORS.values())))
        color.setAlphaF(0.8)
        self.pixmaps[uri] = (Fetching, color)
        return color

    def data(self, index, role=Qt.DisplayRole):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None
        if role == Qt.DisplayRole:
            return self._items[offset].title_display
        elif role == Qt.UserRole:
            song = self._items[offset]
            pixmap = self.get_pixmap_unblocking(song)
            return (song, pixmap)
        return None

    def on_rows_about_to_be_removed(self, _, first, last):
        for i in range(first, last+1):
            item = self._items[i]
            uri = reverse(item)
            # clear pixmap cache
            self.pixmaps.pop(uri, None)


class SongMiniCardListModel(ReaderFetchMoreMixin, BaseSongMiniCardListModel):
    def __init__(self, reader, fetch_image, parent=None):
        super().__init__(fetch_image, parent)

        self._reader = reader
        self._fetch_more_step = 10
        self._is_fetching = False

    @classmethod
    def create(cls, reader, app: 'GuiApp'):
        return cls(create_reader(reader),
                   fetch_image=fetch_cover_wrapper(app))


class SongMiniCardListDelegate(QStyledItemDelegate):
    img_padding = 2

    def __init__(
        self,
        view,
        card_min_width=200,
        card_height=40,
        card_right_spacing=10,
        card_padding=(3, 3, 3, 0),
        hover_color_role=QPalette.Window,
    ):
        """
        QListView.setSpacing set spacing around the item, however, sometimes
        the left spacing is unneeded. `card_left_padding` is used to customize
        the behaviour.
        """
        super().__init__(parent=view)

        self.view = view
        self.card_min_width = card_min_width
        self.card_height = card_height
        self.card_right_spacing = card_right_spacing
        self.hover_color_role = hover_color_role
        self.card_top_padding = card_padding[1]
        self.card_bottom_padding = card_padding[3]
        self.card_left_padding = card_padding[0]

        self._device_pixel_ratio = QGuiApplication.instance().devicePixelRatio()

    def item_sizehint(self) -> tuple:
        # HELP: listview needs about 20 spacing left on macOS
        width = max(self.view.width() - 20, self.card_min_width)

        # according to our algorithm, when the widget width is:
        #   2(card_min_width + card_right_spacing) + card_right_spacing - 1,
        # the card width can take the maximum width, it will be:
        #   CardMaxWidth = 2 * card_min_width + card_right_spacing - 1

        # calculate max column count
        count = (width - self.card_right_spacing) // \
            (self.card_min_width + self.card_right_spacing)
        count = max(count, 1)
        item_width = (width - ((count + 1) * self.card_right_spacing)) // count
        return (
            item_width,
            self.card_height + self.card_top_padding + self.card_bottom_padding
        )

    def paint(self, painter, option, index):
        card_top_padding = self.card_top_padding
        card_right_spacing = self.card_right_spacing
        card_height = self.card_height
        card_left_padding = self.card_left_padding
        border_radius = 3

        rect = option.rect
        # HACK(cosven): from the QFontMetrics doc, there is usually a small spacing
        # between a character and the font rect highest/lowest position.
        # Assume the spacing is 2px here.
        img_padding = self.img_padding
        cover_height = card_height - 2 * img_padding
        cover_width = cover_height
        song, obj = index.data(Qt.UserRole)
        if obj is None:
            return

        selected = option.state & QStyle.State_Selected
        if selected:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(option.palette.color(QPalette.Highlight))
            painter.drawRect(rect)
            painter.restore()
        elif option.state & QStyle.State_MouseOver:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(option.palette.color(self.hover_color_role))
            painter.drawRect(rect)
            painter.restore()

        painter.save()
        painter.translate(rect.x() + card_left_padding, rect.y() + card_top_padding)

        if selected:
            text_color = option.palette.color(QPalette.HighlightedText)
            non_text_color = QColor(text_color)
            non_text_color.setAlpha(200)
        else:
            text_color = option.palette.color(QPalette.Text)
            if text_color.lightness() > 150:
                non_text_color = text_color.darker(140)
            else:
                non_text_color = text_color.lighter(150)
            non_text_color.setAlpha(100)

        # Draw image.
        painter.save()
        painter.translate(0, img_padding)
        self.paint_pixmap(
            painter, non_text_color, obj, cover_width, cover_height, border_radius
        )
        painter.restore()

        # Draw text.
        painter.save()
        text_width = rect.width() - cover_width - \
            card_left_padding * 2 - card_right_spacing
        painter.translate(cover_width + card_left_padding, 0)
        title = index.data(Qt.DisplayRole)
        subtitle = f'{song.artists_name_display} • {song.album_name_display}'
        # Note this is not a bool object.
        is_enabled = option.state & QStyle.State_Enabled
        self.paint_text(
            painter, is_enabled, title, subtitle, text_color, non_text_color, text_width,
            card_height
        )
        painter.restore()

        painter.restore()

    def paint_text(
        self, painter, is_enabled, title, subtitle, text_color, non_text_color,
        text_width, text_height
    ):
        each_height = text_height // 2
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Draw title.
        title_rect = QRectF(0, 0, text_width, each_height)
        fm = QFontMetrics(painter.font())
        if is_enabled:
            painter.setPen(text_color)
        else:
            painter.setPen(non_text_color)
        elided_title = fm.elidedText(title, Qt.ElideRight, int(text_width))
        painter.drawText(title_rect, elided_title, text_option)

        # Draw subtitle.
        painter.translate(0, each_height)
        subtitle_rect = QRectF(0, 0, text_width, each_height)
        elided_title = fm.elidedText(subtitle, Qt.ElideRight, int(text_width))
        font = painter.font()
        resize_font(font, -1)
        painter.setFont(font)
        fm = QFontMetrics(font)
        painter.setPen(non_text_color)
        painter.drawText(subtitle_rect, elided_title, text_option)

    def paint_pixmap(
        self, painter, border_color, decoration, width, height, border_radius
    ):
        painter.setRenderHint(QPainter.Antialiasing)
        pen = painter.pen()
        pen.setColor(border_color)
        painter.setPen(pen)
        if isinstance(decoration, QColor):
            color = decoration
            brush = QBrush(color)
            painter.setBrush(brush)
        else:  # QImage
            if decoration.height() < decoration.width():
                pixmap = decoration.scaledToHeight(
                    int(height * self._device_pixel_ratio), Qt.SmoothTransformation
                )
            else:
                pixmap = decoration.scaledToWidth(
                    int(width * self._device_pixel_ratio), Qt.SmoothTransformation
                )
            pixmap.setDevicePixelRatio(self._device_pixel_ratio)
            brush = QBrush(pixmap)
            painter.setBrush(brush)
        cover_rect = QRect(0, 0, width, height)
        painter.drawRoundedRect(cover_rect, border_radius, border_radius)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.isValid():
            return QSize(*self.item_sizehint())
        return size


class SongMiniCardListView(ItemViewNoScrollMixin, QListView):

    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.setSelectionMode(QListView.ContiguousSelection)
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
