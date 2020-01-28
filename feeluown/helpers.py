"""
feeluown.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""
import asyncio
import sys
import time
import logging
from functools import wraps

try:
    # helper module should work in no-window mode
    from PyQt5.QtCore import QModelIndex, QSize
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPalette
except ImportError:
    pass

logger = logging.getLogger(__name__)


def get_model_type(model):
    return model._meta.model_type


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


class BgTransparentMixin:
    def __init__(self, *args, **kwargs):
        palette = self.palette()
        if sys.platform == 'linux':
            # KDE use the QPalette.Base as background color
            palette.setColor(QPalette.Active, QPalette.Base, Qt.transparent)
            palette.setColor(QPalette.Inactive, QPalette.Base, Qt.transparent)
        else:
            # macOS use the QPalette.Window as background color
            palette.setColor(QPalette.Active, QPalette.Window, Qt.transparent)
            palette.setColor(QPalette.Inactive, QPalette.Window, Qt.transparent)
        self.setPalette(palette)


class ItemViewNoScrollMixin:
    def __init__(self, *args, **kwargs):
        # ItemView class should override these variables as they need
        self._least_row_count = 0
        self._row_height = 0
        self._reserved = 30

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
            self.setFixedHeight(max(height, self._min_height()))
        else:
            self.setFixedHeight(self.sizeHint().height())
        self.updateGeometry()

    def on_rows_changed(self, *args):
        self.adjust_height()

    def setModel(self, model):
        super().setModel(model)

        model.sourceModel().rowsInserted.connect(self.on_rows_changed)
        model.sourceModel().rowsRemoved.connect(self.on_rows_changed)
        self.on_rows_changed()

    def wheelEvent(self, e):
        e.ignore()

    def sizeHint(self):
        height = min_height = self._min_height()
        if self.model() is not None:
            index = self._last_index()
            rect = self.visualRect(index)
            height = rect.y() + rect.height() + self._reserved
            height = max(min_height, height)
        return QSize(self.width(), height)

    def _last_index(self):
        source_model = self.model()
        row_count = source_model.rowCount()
        column_count = source_model.columnCount()
        # can't use createIndex here, why?
        return source_model.index(row_count - 1, column_count - 1)

    def _min_height(self):
        return self._row_height * self._least_row_count + self._reserved
