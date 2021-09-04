"""
feeluown.gui.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""
import asyncio
import itertools
import random
import sys
import time
import logging
from contextlib import suppress
from functools import wraps
from requests.exceptions import RequestException

try:
    # helper module should work in no-window mode
    from PyQt5.QtCore import QModelIndex, QSize, Qt, pyqtSignal, QSortFilterProxyModel, \
        QAbstractListModel
    from PyQt5.QtGui import QPalette, QFontMetrics
    from PyQt5.QtWidgets import QApplication
except ImportError:
    pass

from feeluown.utils import aio
from feeluown.excs import ProviderIOError

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


def use_mac_theme():
    """判断是否需要使用 mac 主题

    目前只是简单为 mac 做一些定制，但如果真的要引入 theme 这个概念，
    单这一个函数是不够的。
    """
    return True
    return sys.platform == 'darwin'


def is_macos():
    """Check if operating system is macOS

    .. versionadded: v3.7.10
    """
    return sys.platform == 'darwin'


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.process_time()
        result = func(*args, **kwargs)
        elapsed_time = time.process_time() - t
        logger.info('function %s executed time: %f s'
                    % (func.__name__, elapsed_time))
        return result
    return wrapper


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


class ItemViewNoScrollMixin:
    """
    `no_scroll_v` means that the itemview's size(height) is always enough to hold
    all fetched items. When new items are fetched, the itemview size is
    automatically adjueted.

    The itemview with no_scroll_v=True is usually used with an outside ScrollArea.
    """
    def __init__(self, *args, no_scroll_v=True, row_height=0, least_row_count=0,
                 reserved=30, **kwargs):
        """
        :params no_scroll_v: enable on no_scroll_v feature or not

        .. versionadded:: 3.7.8
           The *row_height*, *least_row_count*, *reserved* parameter were added.
        """
        self._least_row_count = least_row_count
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
            # according to QAbstractItemView source code,
            # qt will trigger fetchMore when the last row is
            # inside the viewport, so we always hide the last
            # two row to ensure fetch-more will not be
            # triggered automatically
            index = self._last_index()
            rect = self.visualRect(index)
            height = self.sizeHint().height() - int(rect.height() * 1.5) - self._reserved
            self.setFixedHeight(max(height, self.min_height()))
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
            index = self._last_index()
            rect = self.visualRect(index)
            height = rect.y() + rect.height() + self._reserved
            height = max(min_height, height)
        return QSize(super_size_hint.width(), height)

    def _last_index(self):
        source_model = self.model()
        row_count = source_model.rowCount()
        if isinstance(source_model, QAbstractListModel):
            column_count = 1
        else:
            column_count = source_model.columnCount()
        # can't use createIndex here, why?
        return source_model.index(row_count - 1, column_count - 1)

    def min_height(self):
        default = self._row_height * self._least_row_count + self._reserved
        return max(self._min_height, default)

    def suggest_min_height(self, height):
        """
        parent should call this method where it's size changed
        """
        self._min_height = height


def elided_text(text, width):
    font_metrics = QFontMetrics(QApplication.font())
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
                self._fetch_more_cb(None)
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


def fetch_cover_wrapper(img_mgr):
    """
    Your should only use this helper within ImgListModel.
    """
    async def fetch_model_cover(model, cb, uid):
        # try get from cache first
        content = img_mgr.get_from_cache(uid)
        if content is not None:
            return cb(content)
        # FIXME: sleep random second to avoid send too many request to provider
        await asyncio.sleep(random.randrange(100) / 100)
        with suppress(ProviderIOError, RequestException):
            cover = await async_run(lambda: model.cover)
            if cover:  # check if cover url is valid
                # FIXME: we should check if cover is a media object
                if not isinstance(cover, str):
                    cover = cover.url
            url = cover
            if url:
                content = await img_mgr.get(url, uid)
                cb(content)
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
