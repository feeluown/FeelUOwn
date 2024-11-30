# mypy: disable-error-code=attr-defined
#
# HELP: Disable mypy check(attr-defined) since there is no good way to
# typing a Mixin class like ItemViewNoScroll: https://github.com/python/typing/issues/213
#
# TODO(cosven): Such mixin class(like ItemViewNoScrollMixin) has little reable and
# it's hard to typing. I think we can split it into a delegate and a mixin to solve
# this problem.
#
# For example::
#
#     class ItemViewNoScrollManager: ...
#     class ItemViewNoScrollMixin: ...
#     class ListView(ItemViewNoScrollMixin, QListView):
#         def __init__(self):
#             self.no_scroll_manager = ItemViewNoScrollManager(self)
#     class NoScrollableItemView(Protocol):
#         no_scroll_manager: ItemViewNoScrollManager

from __future__ import annotations
import asyncio
import random
import sys
import logging
from contextlib import contextmanager
from typing import TypeVar, List, Optional, Generic, Union, cast, TYPE_CHECKING

from PyQt5.QtCore import QModelIndex, QSize, Qt, pyqtSignal, QSortFilterProxyModel, \
    QAbstractListModel, QPoint
from PyQt5.QtGui import QPalette, QFontMetrics, QColor, QPainter, QMouseEvent, \
    QKeySequence
from PyQt5.QtWidgets import QApplication, QScrollArea, QWidget, QShortcut, \
    QAbstractScrollArea

from feeluown.utils.aio import run_afn, run_fn
from feeluown.utils.reader import AsyncReader, Reader
from feeluown.utils.typing_ import Protocol
from feeluown.excs import ProviderIOError, ResourceNotFound
from feeluown.library import ModelNotFound, ModelType, BaseModel
from feeluown.library import reverse
from feeluown.gui.consts import FontFamilies


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


logger = logging.getLogger(__name__)
T = TypeVar("T")

IS_MACOS = sys.platform == 'darwin'


def darker_or_lighter(color: QColor, factor):
    """
    If the color is a light color, for example, white, then this returns
    a darker color.
    """
    if color.lightness() > 150:
        return color.darker(factor)
    return color.lighter(factor)


async def async_run(func, loop=None, executor=None):
    """异步的获取 model 属性值

    值得注意的是，如果 executor 消费队列排队了，这个会卡住。
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func)


class ActionError(Exception):
    pass


def get_qapp() -> QApplication:
    return cast(QApplication, QApplication.instance())


def is_macos():
    """Check if operating system is macOS

    .. versionadded: v3.7.10
    """
    return sys.platform == 'darwin'


def disconnect_slots_if_has(signal):
    try:
        signal.disconnect()
    except TypeError:  # signal has no slots
        pass


def resize_font(font, delta):
    if font.pixelSize() > 0:
        font.setPixelSize(max(1, font.pixelSize() + delta))
    else:
        font.setPointSize(max(1, font.pointSize() + delta))


def palette_set_bg_color(palette, color):
    """set palette background color"""
    if sys.platform == 'linux':
        # KDE use the QPalette.Base as background color
        palette.setColor(QPalette.Active, QPalette.Base, color)
        palette.setColor(QPalette.Inactive, QPalette.Base, color)
        # GNOME use the QPalette.Window as background color
        palette.setColor(QPalette.Active, QPalette.Window, color)
        palette.setColor(QPalette.Inactive, QPalette.Window, color)
    else:
        # macOS use the QPalette.Window as background color
        palette.setColor(QPalette.Active, QPalette.Window, color)
        palette.setColor(QPalette.Inactive, QPalette.Window, color)


def unify_scroll_area_style(scroll_area: QAbstractScrollArea):
    if not IS_MACOS:
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


def set_widget_bg_transparent(widget: QWidget):
    palette = widget.palette()
    palette_set_bg_color(palette, Qt.transparent)
    widget.setPalette(palette)


class BgTransparentMixin:
    def __init__(self: QWidget, *args, **kwargs):  # type: ignore[misc]
        palette = self.palette()
        palette_set_bg_color(palette, Qt.transparent)
        self.setPalette(palette)


class BaseScrollAreaForNoScrollItemView(QScrollArea):
    """A scroll area base class for itemview with no_scroll_v=True

    Subclass must implement the following methods:
    * itemview
    * height_for_itemview
    Also note the API is not stable.

    .. versionadded:: 3.8.9
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.verticalScrollBar().valueChanged.connect(self.on_v_scrollbar_value_changed)

    def get_itemview(self):
        raise NotImplementedError

    def height_for_itemview(self):
        raise NotImplementedError

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.maybe_resize_itemview()

    def maybe_resize_itemview(self):
        """Resize itemview to make sure it has a chance to fetch more items

        When the itemview has no more items, do not need to resize it.
        """
        itemview = self.get_itemview()
        if itemview is not None:
            model = itemview.model()
            if model is not None and model.canFetchMore(QModelIndex()):
                # +1 to make sure user can scroll, then user has a change to
                # trigger itemview fetch more.
                itemview.suggest_min_height(self.height_for_itemview() + 1)
                itemview.adjust_height()

    def maybe_trigger_itemview_fetch_more(self):
        itemview = self.get_itemview()
        if itemview is not None:
            model = itemview.model()
            if model is not None and model.canFetchMore(QModelIndex()):
                model.fetchMore(QModelIndex())

    def on_v_scrollbar_value_changed(self, value):
        maximum = self.verticalScrollBar().maximum()
        if maximum == value:
            self.maybe_trigger_itemview_fetch_more()


class ItemViewNoScrollMixin:
    """
    `no_scroll_v` means that the itemview's size(height) is always enough to hold
    all fetched items. When new items are fetched, the itemview size is
    automatically adjueted.

    The itemview with no_scroll_v=True is usually used with an outside ScrollArea.

    Python Notes::

        ItemViewNoScrollMixin follows the "cooperative multi-inheritance" pattern.
        Since ItemViewNoScrollMixin use some QObject API, subclass should consider
        the MRO order. In other words, ItemViewNoScrollMixin should be the parent
        class of QObject. XWidget(ItemViewNoScrollMixin, QObject) is a good choice,
        and XWidget(QObject, ItemViewNoScrollMixin) is not.
    """
    def __init__(self, *args, no_scroll_v=True, row_height=0, least_row_count=0,
                 fixed_row_count=0, reserved=30, **kwargs):
        """
        :params no_scroll_v: enable on no_scroll_v feature or not
        :params fixed_row_count: set row_height when fixed_row_count is set

        .. versionadded:: 3.7.8
           The *row_height*, *least_row_count*, *reserved* parameter were added.

        .. versionadded:: 3.8.9
           The *fixed_row_count* parameter was added.
        """
        super().__init__(**kwargs)  # Cooperative multi-inheritance.
        self._least_row_count = least_row_count
        self._fixed_row_count = fixed_row_count
        self._row_height = row_height
        self._reserved = reserved

        self._min_height = 0

        self._no_scroll_v = no_scroll_v

    def initialize(self):
        """
        .. versionadded:: 3.7.7
        """
        if self._no_scroll_v is True:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # def set_no_scroll_v(self, no_scroll_v):
    #     """
    #     .. versionadded:: 3.7.7
    #     """
    #     self._no_scroll_v = no_scroll_v
    #     if no_scroll_v is True:
    #         self.adjust_height()
    #         self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def adjust_height(self):
        if self.model() is None:
            return

        if self.model().canFetchMore(QModelIndex()):
            if self._fixed_row_count == 0:
                # according to QAbstractItemView source code,
                # qt will trigger fetchMore when the last row is
                # inside the viewport, so we always hide the last
                # two row to ensure fetch-more will not be
                # triggered automatically.
                #
                # qt triggers fetchMore when user scrolls down to bottom.
                index = self._last_visible_index()
                rect = self.visualRect(index)
                height = self.sizeHint().height()
                if self._no_scroll_v is False:
                    height = height - int(rect.height() * 1.5) - self._reserved
                self.setFixedHeight(max(height, self.min_height()))
            else:
                self.setFixedHeight(self._row_height * self._fixed_row_count)
        else:
            height = self.sizeHint().height()
            self.setFixedHeight(height)
        self.updateGeometry()

    def on_rows_changed(self, *args):
        if self._no_scroll_v is True:
            self.adjust_height()

    def setModel(self, model):
        super().setModel(model)  # type: ignore[misc]
        if model is None:
            return
        model.rowsInserted.connect(self.on_rows_changed)
        model.rowsRemoved.connect(self.on_rows_changed)
        if isinstance(model, QSortFilterProxyModel):
            srcModel = model.sourceModel()
            if isinstance(srcModel, ReaderFetchMoreMixin):
                srcModel.no_more_item.connect(self.on_rows_changed)
        self.on_rows_changed()

    def wheelEvent(self, e):
        if self._no_scroll_v is True:
            if abs(e.angleDelta().x()) > abs(e.angleDelta().y()):
                QApplication.sendEvent(self.horizontalScrollBar(), e)
            else:
                e.ignore()  # let parents handle it
        else:
            super().wheelEvent(e)  # type: ignore[misc]

    def sizeHint(self):
        super_size_hint = super().sizeHint()  # type: ignore[misc]
        if self._no_scroll_v is False:
            return super_size_hint

        height = min_height = self.min_height()
        if self.model() is not None:
            if self._fixed_row_count == 0:
                index = self._last_visible_index()
                rect = self.visualRect(index)
                height = rect.y() + rect.height() + self._reserved
                height = max(min_height, height)
            else:
                height = self._row_height * self._fixed_row_count
        return QSize(super_size_hint.width(), height)

    def _last_visible_index(self):
        source_model = self.model()
        row_index = source_model.rowCount() - 1
        if isinstance(source_model, QAbstractListModel):
            column_index = 0
        else:
            column_index = source_model.columnCount() - 1
            while column_index >= 0:
                index = source_model.index(row_index, column_index)
                if not self.isIndexHidden(index):
                    break
                column_index -= 1
        # can't use createIndex here, why?
        return source_model.index(row_index, column_index)

    def min_height(self):
        default = self._row_height * self._least_row_count + self._reserved
        return max(self._min_height, default)

    def suggest_min_height(self, height):
        """
        parent should call this method where it's size changed
        """
        self._min_height = height


def elided_text(text, width, font=None):
    if font is None:
        font = QApplication.font()
    font_metrics = QFontMetrics(font)
    return font_metrics.elidedText(text, Qt.ElideRight, width)


class Paddings(tuple):
    def __new__(cls, *sequence):
        assert len(sequence) == 4
        return super().__new__(cls, tuple(sequence))

    @property
    def left(self):
        return self[0]

    @property
    def top(self):
        return self[1]

    @property
    def right(self):
        return self[2]

    @property
    def bottom(self):
        return self[3]

    @property
    def height(self):
        return self[1] + self[3]

    @property
    def width(self):
        return self[0] + self[2]


Margins = Paddings


# HELP(cosven): please help remove duplicate code between ReaderFetchMoreMixin
# and this class.
class ModelUsingReader(Protocol[T]):
    _reader: Union[Reader[T], AsyncReader]
    _items: List[T]
    _fetch_more_step: int
    _is_fetching: bool

    def rowCount(self) -> int: ...
    def beginInsertRows(self, _, __, ___): ...
    def endInsertRows(self): ...
    def canFetchMore(self, _) -> bool: ...
    def fetchMore(self, _): ...
    def can_fetch_more(self, _=None) -> bool: ...
    def fetch_more_impl(self): ...
    def on_items_fetched(self, items: List[T]): ...
    def _fetch_more_cb(self, items: Optional[List[T]]): ...
    def _async_fetch_cb(self, future): ...


class ReaderFetchMoreMixin(Generic[T]):
    """
    The class should implement

    1. _reader
    2. _items
    3. _fetch_more_step
    4. _is_fetching
    """
    no_more_item = pyqtSignal()

    def get_reader(self: ModelUsingReader[T]):
        return self._reader

    def canFetchMore(self: ModelUsingReader[T], _):
        return self.can_fetch_more()

    def fetchMore(self: ModelUsingReader[T], _):
        if self._is_fetching is False:
            self._is_fetching = True
            self.fetch_more_impl()

    def can_fetch_more(self: ModelUsingReader[T], _=None):
        reader = cast(Reader, self._reader)
        count = reader.count
        if count is not None:
            return count > self.rowCount()

        # The reader sets the count when it has no more items,
        # so it is safe to return True here
        return True

    def fetch_more_impl(self: ModelUsingReader[T]):
        """fetch more items from reader
        """
        reader = self._reader
        step = self._fetch_more_step

        if isinstance(reader, AsyncReader):
            async def fetch():
                items = []
                count = 0
                async for item in reader:  # type: ignore
                    items.append(item)
                    count += 1
                    if count == step:
                        break
                return items
            task = run_afn(fetch)
        else:
            assert isinstance(reader, Reader)
            task = run_fn(reader.read_range, self.rowCount(), step + self.rowCount())
        task.add_done_callback(self._async_fetch_cb)

    def on_items_fetched(self: ModelUsingReader[T], items: List[T]):
        begin = len(self._items)
        end = begin + len(items) - 1
        self.beginInsertRows(QModelIndex(), begin, end)
        self._items.extend(items)
        self.endInsertRows()

    def _fetch_more_cb(self: ModelUsingReader[T], items: Optional[List[T]]):
        self._is_fetching = False
        if items is not None:
            self.on_items_fetched(items)

    def _async_fetch_cb(self: ModelUsingReader[T], future):
        try:
            items = future.result()
        except ProviderIOError as e:
            logger.error(f'async fetch more items failed, reason: {e}')
            self._fetch_more_cb(None)
        except:  # noqa
            logger.exception('async fetch more items failed')
            self._fetch_more_cb(None)
        else:
            if not items:
                # The reader should not return empty list when fetching more items,
                # maybe something wrong with the reader.
                logger.warning('async fetch more items return empty list')
            self._fetch_more_cb(items)


def fetch_cover_wrapper(app: GuiApp):
    """
    Your should only use this helper within ImgListModel and SongMiniCardListModel.
    """
    img_mgr, library = app.img_mgr, app.library

    async def fetch_image_with_cb(img_uid, img_url, cb):
        # Fetch image by url and invoke cb.
        if img_url:
            # FIXME: sleep random second to avoid send too many request to provider
            await asyncio.sleep(random.randrange(100) / 100)
            content = await img_mgr.get(img_url, img_uid)
            cb(content)
        else:
            cb(None)

    async def fetch_song_pic_from_album(album, cb):
        if album is not None:
            await fetch_other_model_cover(album, cb)
        else:
            cb(None)

    async def fetch_song_pic_url(model, cb):
        """
        The song may be a v2 brief model or a v1 model.
        """
        is_v2_model = isinstance(model, BaseModel)

        # If the song is a v1 model, just fallback to use its album cover.
        if not is_v2_model:
            try:
                upgraded_song = await run_fn(library.song_upgrade, model)
            except ModelNotFound:
                cb(None)
            else:
                await fetch_song_pic_from_album(upgraded_song.album, cb)
            return

        # v2 song model has its own image(pic_url), check if it is in cache first.
        cache_key = 'album_cover_uid'
        song_img_uid = reverse(model) + '/pic_url'
        album_img_uid, _ = model.cache_get(cache_key)
        for img_uid in (song_img_uid, album_img_uid):
            if img_uid:
                content = img_mgr.get_from_cache(img_uid)
                if content is not None:
                    cb(content)
                    return

        # Image is not in cache.
        try:
            upgraded_song = await run_fn(library.song_upgrade, model)
        except ResourceNotFound:
            cb(None)
        else:
            # Try to fetch with pic_url first.
            # Note that some providers may not provide pic_url for songs.
            if upgraded_song.pic_url:
                img_uid = reverse(model) + '/pic_url'
                img_url = upgraded_song.pic_url
                return await fetch_image_with_cb(img_uid, img_url, cb)

            album = upgraded_song.album
            if album is None:
                cb(None)
                return

            album_img_uid = reverse(album) + '/cover'
            model.cache_set(cache_key, album_img_uid)
            return await fetch_song_pic_from_album(album, cb)

    async def fetch_other_model_cover(model, cb):
        img_uid = reverse(model) + '/cover'

        # Check image cache with image unique ID.
        content = img_mgr.get_from_cache(img_uid)
        if content is not None:
            cb(content)
            return

        img_url = await run_fn(library.model_get_cover, model)
        return await fetch_image_with_cb(img_uid, img_url, cb)

    async def fetch_model_cover(model, cb):
        if ModelType(model.meta.model_type) is ModelType.song:
            return await fetch_song_pic_url(model, cb)
        return await fetch_other_model_cover(model, cb)

    return fetch_model_cover


def random_solarized_color():
    return QColor(random.choice(list(SOLARIZED_COLORS.values())))


@contextmanager
def painter_save(painter: QPainter):
    painter.save()
    yield
    painter.restore()


def secondary_text_color(palette: QPalette):
    text_color: QColor = palette.color(QPalette.Text)
    if text_color.lightness() > 150:
        non_text_color = text_color.darker(140)
    else:
        non_text_color = text_color.lighter(150)
    non_text_color.setAlpha(100)
    return non_text_color


class ClickableMixin:
    clicked = pyqtSignal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Cooperative multi-inheritance.

        self._down = False

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() != Qt.LeftButton:
            # Call super.mousePressEvent because the concrete class may do sth inside it.
            super().mousePressEvent(e)
            return
        if self._hit_button(e.pos()):
            self._down = True
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() != Qt.LeftButton or not self._down:
            super().mouseReleaseEvent(e)
            return
        self._down = False
        if self._hit_button(e.pos()):
            self.clicked.emit()
            e.accept()
        else:
            super().mouseReleaseEvent(e)

    def _hit_button(self, pos: QPoint):
        return self.rect().contains(pos)

    def set_down(self, down: bool):
        self._down = down


def set_default_font_families(widget):
    font = widget.font()
    font.setFamilies(FontFamilies)
    widget.setFont(font)


def esc_hide_widget(widget):
    QShortcut(QKeySequence.Cancel, widget).activated.connect(widget.hide)


# https://ethanschoonover.com/solarized/
# Do not change the existing colors if they are used by some widgets/components.
SOLARIZED_COLORS = {
    'yellow':    '#b58900',
    'orange':    '#cb4b16',
    'red':       '#dc322f',
    'magenta':   '#d33682',
    'violet':    '#6c71c4',
    'blue':      '#268bd2',
    'cyan':      '#2aa198',
    'green':     '#859900',
}
