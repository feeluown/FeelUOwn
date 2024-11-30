"""
ImgList model and delegate

- ImgCardListDelegate
- ImgCardListModel

By default, we think the proper width of a cover is about 160px,
the margin between two cover should be about 20px. When the view is
resized, the cover width and the margin should make a few adjustment.
"""

# pylint: disable=unused-argument
import logging
import random
from typing import TypeVar, Optional, List, cast, Union, TYPE_CHECKING

from PyQt5.QtCore import (
    QAbstractListModel, QModelIndex, Qt, QObject, QEvent,
    QRectF, QRect, QSize, QSortFilterProxyModel, pyqtSignal
)
from PyQt5.QtGui import (
    QImage, QColor, QResizeEvent, QGuiApplication,
    QBrush, QPainter, QTextOption, QFontMetrics
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate, QListView, QFrame,
)

from feeluown.utils import aio
from feeluown.library import AlbumModel, AlbumType, PlaylistModel, VideoModel
from feeluown.utils.reader import wrap, create_reader
from feeluown.utils.utils import int_to_human_readable
from feeluown.library import reverse
from feeluown.gui.helpers import (
    ItemViewNoScrollMixin, resize_font, ReaderFetchMoreMixin, painter_save,
    secondary_text_color, fetch_cover_wrapper
)

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

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


class ImgCardListModel(QAbstractListModel, ReaderFetchMoreMixin[T]):
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

    @classmethod
    def create(cls, reader, app: 'GuiApp'):
        return cls(create_reader(reader),
                   fetch_image=fetch_cover_wrapper(app))

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
        elif role == Qt.ToolTipRole:
            return item.name
        return None


class ImgCardListDelegate(QAbstractItemDelegate):
    """
    Card layout should be like the following::

        |card0    card1    card2|
                                          <- vertical spacing
        |card3    card4    card5|
                                          <- vertical spacing

    The leftmost cards should have a half_h_spacing on the right side,
    and the rightmost cards should have a half_h_spacing on the left side.
    Middle cards should have a half_h_spacing on both sides.
    """
    def __init__(self, parent=None,
                 card_min_width=150, card_spacing=20, card_text_height=40,
                 **_):
        super().__init__(parent)

        self.view: 'ImgCardListView' = parent
        self.view.installEventFilter(self)
        self.as_circle = True
        self.w_h_ratio = 1.0

        self._device_pixel_ratio = QGuiApplication.instance().devicePixelRatio()

        self.card_min_width = card_min_width
        self.card_spacing = card_spacing
        self.card_text_height = card_text_height

        self.h_spacing = self.card_spacing
        self.v_spacing = self.half_h_spacing = self.h_spacing // 2
        self.text_height = self.card_text_height

        # These variables are calculated in on_view_resized().
        self._card_width = self._card_height = 0
        self._view_width = 0

    def update_settings(self, name, value):
        assert hasattr(self, name), f"no such setting: {name}"
        setattr(self, name, value)
        self.re_calc_all()
        self.view.update()

    def paint(self, painter, option, index):
        obj: Optional[Union[QImage, QColor]] = index.data(Qt.DecorationRole)
        if obj is None:
            return

        with painter_save(painter):
            painter.setRenderHints(QPainter.Antialiasing |
                                   QPainter.SmoothPixmapTransform |
                                   QPainter.LosslessImageRendering)
            painter.translate(option.rect.x(), option.rect.y())

            if not self.is_leftmost(index):
                painter.translate(self.half_h_spacing, 0)

            spacing = self.get_card_h_spacing(index)
            draw_width = option.rect.width() - spacing

            secondary_color = border_color = secondary_text_color(option.palette)
            # Draw cover or color.
            img_height = int(draw_width / self.w_h_ratio)
            with painter_save(painter):
                self.draw_img_or_color(
                    painter, border_color, obj, draw_width, img_height)

            # Draw text(album name / artist name / playlist name), and draw source.
            text_title_height = 30
            text_source_height = self.text_height - text_title_height
            painter.translate(0, img_height)
            text_rect = QRectF(0, 0, draw_width, text_title_height)
            with painter_save(painter):
                self.draw_title(painter, index, text_rect)
            painter.translate(0, text_title_height - 5)
            with painter_save(painter):
                self.draw_whats_this(painter,
                                     index,
                                     secondary_color,
                                     QRectF(0, 0, draw_width, text_source_height + 5))

    def draw_img_or_color(self, painter, border_color, obj, draw_width, height):
        pen = painter.pen()
        pen.setColor(border_color)
        painter.setPen(pen)
        if isinstance(obj, QColor):
            color = obj
            brush = QBrush(color)
            painter.setBrush(brush)
        else:
            if obj.width() / obj.height() > draw_width / height:
                img = obj.scaledToHeight(int(height * self._device_pixel_ratio),
                                         Qt.SmoothTransformation)
            else:
                img = obj.scaledToWidth(int(draw_width * self._device_pixel_ratio),
                                        Qt.SmoothTransformation)
            img.setDevicePixelRatio(self._device_pixel_ratio)
            brush = QBrush(img)
            painter.setBrush(brush)
        border_radius = 3
        if self.as_circle:
            border_radius = draw_width // 2
        cover_rect = QRect(0, 0, draw_width, height)
        painter.drawRoundedRect(cover_rect, border_radius, border_radius)

    def draw_title(self, painter, index, text_rect):
        text_option = QTextOption()
        if self.as_circle:
            text_option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            text_option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name = index.data(Qt.DisplayRole)
        fm = QFontMetrics(painter.font())
        elided_name = fm.elidedText(name, Qt.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect, elided_name, text_option)

    def draw_whats_this(self, painter, index, non_text_color, whats_this_rect):
        source_option = QTextOption()
        if self.as_circle:
            source_option.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        else:
            source_option.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        whats_this = index.data(Qt.WhatsThisRole)
        pen = painter.pen()
        font = painter.font()
        resize_font(font, -2)
        painter.setFont(font)
        pen.setColor(non_text_color)
        painter.setPen(non_text_color)
        painter.drawText(whats_this_rect, whats_this, source_option)

    def sizeHint(self, option, index):
        spacing = self.get_card_h_spacing(index)
        width = self._card_width
        if index.isValid():
            height = int(width / self.w_h_ratio) + self.text_height
            return QSize(width + spacing, height + self.v_spacing)
        return super().sizeHint(option, index)

    def on_view_resized(self, size: QSize, _: QSize):
        self._view_width = size.width()
        self.re_calc_all()

    def re_calc_all(self):
        # HELP: CardListView needs about 20 spacing left on macOS
        width = max(0, self._view_width - 20)
        card_spacing = self.card_spacing

        # according to our algorithm, when the widget width is:
        #   2(card_min_width + card_spacing) + card_spacing - 1,
        # the cover width can take the maximum width, it will be:
        #   CoverMaxWidth = 2 * card_min_width + card_spacing - 1

        # calculate max column count
        count = (width + card_spacing) // (self.card_min_width + card_spacing)
        count = max(count, 1)
        # calculate img_width when column count is the max
        self._card_width = (width + card_spacing) // count - card_spacing
        self._card_height = int(self._card_width * self.w_h_ratio) + self.text_height
        self.view._row_height = self._card_height + self.v_spacing

    def column_count(self):
        return (self._view_width + self.card_spacing) // \
            (self._card_width + self.card_spacing)

    def which_column(self, index: QModelIndex):
        if not self.view.isWrapping():
            return index.row()
        return index.row() % self.column_count()

    def which_row(self, index: QModelIndex):
        if not self.view.isWrapping():
            return 0
        return index.row() // self.column_count()

    def is_leftmost(self, index):
        return self.which_column(index) == 0

    def is_rightmost(self, index):
        if self.view.isWrapping():
            return self.which_column(index) == self.column_count() - 1
        return False  # HELP: no way to check if it is the rightmost.

    def get_card_h_spacing(self, index):
        if self.is_leftmost(index) or self.is_rightmost(index):
            return self.half_h_spacing
        return self.h_spacing

    def eventFilter(self, _: QObject, event: QEvent):
        if event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.on_view_resized(event.size(), event.oldSize())
        return False


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
        source_model = cast(ImgCardListModel, self.sourceModel())
        index = source_model.index(source_row, parent=source_parent)
        artist = index.data(Qt.UserRole)
        if self.text:
            accepted = self.text.lower() in artist.name_display.lower()
        return accepted


class ImgCardListView(ItemViewNoScrollMixin, QListView):
    """
    .. versionchanged:: 3.9
       The *card_min_width*, *card_spacing*, *card_text_height* parameter were removed.
    """
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        # Override ItemViewNoScrollMixin variables. Actually, there variables are
        # not important because ItemViewNoScrollMixin use QListView.sizeHint() to
        # calculate the size and it works well.
        #
        #
        self._least_row_count = 1
        self._row_height = 0

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setFrameShape(QFrame.NoFrame)
        self.initialize()

        self.activated.connect(self.on_activated)

    def on_activated(self, _: QModelIndex):
        """
        Subclass can implement this method if needed.
        """
        pass


class VideoCardListModel(ImgCardListModel):
    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None
        video = self._items[offset]
        if role == Qt.DisplayRole:
            return video.title
        elif role == Qt.ToolTipRole:
            return video.title
        elif (
            role == Qt.WhatsThisRole
            and isinstance(video, VideoModel)
            and video.play_count > 0
        ):
            return f'► {int_to_human_readable(video.play_count)}'
        return super().data(index, role)


class VideoCardListDelegate(ImgCardListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False
        self.w_h_ratio = 1.618


class VideoFilterProxyModel(ImgFilterProxyModel):
    pass


class VideoCardListView(ImgCardListView):
    play_video_needed = pyqtSignal([object])

    def on_activated(self, index):
        video = index.data(Qt.UserRole)
        self.play_video_needed.emit(video)


class PlaylistCardListModel(ImgCardListModel):
    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None

        playlist = self._items[offset]
        if (
            role == Qt.WhatsThisRole
            and isinstance(playlist, PlaylistModel)
            and playlist.play_count > 0
        ):
            count = int_to_human_readable(playlist.play_count)
            return f'► {count}'
        return super().data(index, role)


class PlaylistCardListDelegate(ImgCardListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False


class PlaylistFilterProxyModel(ImgFilterProxyModel):
    pass


class PlaylistCardListView(ImgCardListView):
    show_playlist_needed = pyqtSignal([object])

    def on_activated(self, index):
        artist = index.data(Qt.UserRole)
        self.show_playlist_needed.emit(artist)


class ArtistCardListModel(ImgCardListModel):
    pass


class ArtistCardListDelegate(ImgCardListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = True


class ArtistFilterProxyModel(ImgFilterProxyModel):
    pass


class ArtistCardListView(ImgCardListView):
    show_artist_needed = pyqtSignal([object])

    def on_activated(self, index):
        artist = index.data(Qt.UserRole)
        self.show_artist_needed.emit(artist)


class AlbumCardListModel(ImgCardListModel):
    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None

        album = self._items[offset]
        if role == Qt.WhatsThisRole:
            if isinstance(album, AlbumModel):
                if album.song_count >= 0:
                    # Like: 1991-01-01 10首
                    return f'{album.released} {album.song_count}首'
                return album.released
        return super().data(index, role)


class AlbumCardListDelegate(ImgCardListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False


class AlbumFilterProxyModel(ImgFilterProxyModel):
    def __init__(self, parent=None, types=None):
        super().__init__(parent)

        self.types = types

    def filter_by_types(self, types):
        # if types is a empty list or None, we show all albums
        if not types:
            types = None
        self.types = types
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        accepted = super().filterAcceptsRow(source_row, source_parent)
        source_model = self.sourceModel()
        assert isinstance(source_model, AlbumCardListModel)
        index = source_model.index(source_row, parent=source_parent)
        album = index.data(Qt.UserRole)
        if accepted and self.types:
            accepted = AlbumType(album.type_) in self.types
        return accepted


class AlbumCardListView(ImgCardListView):
    show_album_needed = pyqtSignal([object])

    def on_activated(self, index):
        album = index.data(Qt.UserRole)
        self.show_album_needed.emit(album)
