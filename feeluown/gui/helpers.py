"""
feeluown.gui.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""
import asyncio
import itertools
import random
import sys
import logging

try:
    # helper module should work in no-window mode
    from PyQt5.QtCore import QModelIndex, QSize, Qt, pyqtSignal, QSortFilterProxyModel, \
        QAbstractListModel
    from PyQt5.QtGui import QPalette, QFontMetrics
    from PyQt5.QtWidgets import QApplication, QScrollArea
except ImportError:
    pass

from feeluown.utils import aio
from feeluown.excs import ProviderIOError
from feeluown.library import NotSupported, ModelType, BaseModel
from feeluown.models.uri import reverse

logger = logging.getLogger(__name__)


async def async_run(func, loop=None, executor=None):
    """异步的获取 model 属性值

    值得注意的是，如果 executor 消费队列排队了，这个会卡住。
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func)


class ActionError(Exception):
    pass


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


class BgTransparentMixin:
    def __init__(self, *args, **kwargs):
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
                # triggered automatically
                index = self._last_visible_index()
                rect = self.visualRect(index)
                height = self.sizeHint().height() - int(rect.height() * 1.5) - \
                    self._reserved
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
        super().setModel(model)
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
            super().wheelEvent(e)

    def sizeHint(self):
        super_size_hint = super().sizeHint()
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


class ReaderFetchMoreMixin:
    """
    The class should implement

    1. _reader
    2. _items
    3. _fetch_more_step
    4. _is_fetching
    """
    no_more_item = pyqtSignal()

    def canFetchMore(self, _=None):
        return self.can_fetch_more()

    def fetchMore(self, _=None):
        if self._is_fetching is False:
            self._is_fetching = True
            self.fetch_more_impl()

    def can_fetch_more(self, _=None):
        reader = self._reader

        count = reader.count
        if count is not None:
            return count > self.rowCount()

        # The reader sets the count when it has no more items,
        # so it is safe to return True here
        return True

    def fetch_more_impl(self):
        """fetch more items from reader
        """
        reader = self._reader
        step = self._fetch_more_step

        if reader.is_async:
            async def fetch():
                items = []
                count = 0
                async for item in reader:
                    items.append(item)
                    count += 1
                    if count == step:
                        break
                return items
            future = aio.create_task(fetch())
            future.add_done_callback(self._async_fetch_cb)
        else:
            try:
                items = list(itertools.islice(reader, step))
            except ProviderIOError:
                logger.exception('fetch more items failed')
                self._fetch_more_cb([])
            else:
                self._fetch_more_cb(items)

    def on_items_fetched(self, items):
        begin = len(self._items)
        end = begin + len(items) - 1
        self.beginInsertRows(QModelIndex(), begin, end)
        self._items.extend(items)
        self.endInsertRows()

    def _fetch_more_cb(self, items):
        self._is_fetching = False
        if items is None:
            return
        self.on_items_fetched(items)

    def _async_fetch_cb(self, future):
        try:
            items = future.result()
        except:  # noqa
            logger.exception('async fetch more items failed')
            self._fetch_more_cb(None)
        else:
            self._fetch_more_cb(items)


def fetch_cover_wrapper(app):
    """
    Your should only use this helper within ImgListModel and SongMiniCardListModel.
    """
    img_mgr, library = app.img_mgr, app.library

    async def fetch_model_cover(model, cb):
        # Get image unique id.
        model_is_song = False
        song_is_v2 = False
        upgraded_song = None
        if ModelType(model.meta.model_type) is ModelType.song:
            model_is_song = True
            if isinstance(model, BaseModel):
                song_is_v2 = True
                img_uid, _ = model.cache_get('album_uid')
            else:
                img_uid = None
        else:
            img_uid = reverse(model) + '/cover'
        if img_uid is None:
            assert model_is_song
            try:
                upgraded_song = await aio.run_fn(library.song_upgrade, model)
                album = upgraded_song.album
            except NotSupported:
                album = None
            if album is None:
                cb(None)
                return

            img_uid = reverse(album) + '/cover'
            if song_is_v2:
                model.cache_set('album_uid', img_uid)

        # Check image cache with image unique ID.
        content = img_mgr.get_from_cache(img_uid)
        if content is not None:
            cb(content)
            return

        # Get image url.
        img_url = None
        if model_is_song and song_is_v2:
            img_url, _ = model.cache_get('album_cover')
        if img_url is None:
            if model_is_song:
                model_with_img = upgraded_song.album
            else:
                model_with_img = model
            try:
                img_url = await aio.run_fn(library.model_get_cover, model_with_img)
            except NotSupported:
                img_url = ''
            if model_is_song:
                model.cache_set('album_cover', img_url)

        # Fetch image by url and invoke cb.
        if img_url:
            # FIXME: sleep random second to avoid send too many request to provider
            await asyncio.sleep(random.randrange(100) / 100)
            content = await img_mgr.get(img_url, img_uid)
            cb(content)
        else:
            cb(None)

    return fetch_model_cover


# https://ethanschoonover.com/solarized/
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
