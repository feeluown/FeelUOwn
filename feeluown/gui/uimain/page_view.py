import sys

from PyQt5.QtCore import Qt, QRect, QSize, QModelIndex
from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPalette
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QStackedLayout

from feeluown.utils import aio
from feeluown.models import ModelType
from feeluown.utils.reader import wrap

from feeluown.collection import CollectionType
from feeluown.gui.theme import Light
from feeluown.gui.helpers import BgTransparentMixin, ItemViewNoScrollMixin
from feeluown.gui.uimain.toolbar import BottomPanel
from feeluown.gui.page_containers.table import TableContainer
from feeluown.gui.page_containers.collection import CollectionContainer


def add_alpha(color, alpha):
    new_color = QColor(color)
    new_color.setAlpha(alpha)
    return new_color


class ScrollArea(QScrollArea, BgTransparentMixin):
    """
    该 ScrollArea 和 TableContainer 是紧密耦合的一个组件，
    目标是为了让整个 Table 内容都处于一个滚动的窗口内。

    TODO: 给这个 ScrollArea 添加更多注释，对它进行一些重构
    """
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self.t = TableContainer(app, self)
        self.setWidget(self.t)

        self.verticalScrollBar().valueChanged.connect(self.on_v_scrollbar_value_changed)
        # As far as I know, KDE and GNOME can't auto hide the scrollbar,
        # and they show an old-fation vertical scrollbar.
        # HELP: implement an auto-hide scrollbar for Linux
        if sys.platform.lower() != 'darwin':
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def on_v_scrollbar_value_changed(self, value):
        maximum = self.verticalScrollBar().maximum()
        if maximum == value:
            table = self.t.current_table
            if table is None:
                return
            model = table.model()
            if model is not None and model.canFetchMore(QModelIndex()):
                model.fetchMore(QModelIndex())

    def wheelEvent(self, e):
        super().wheelEvent(e)
        self._app.ui.bottom_panel.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        table = self.t.current_table
        if table is not None and isinstance(table, ItemViewNoScrollMixin):
            table.suggest_min_height(self.height_for_table())

    def height_for_table(self):
        """a proper height for the table widget"""
        # spacing is 10
        table_container = self.t
        table_proper_height = self.height() - 10
        if table_container.meta_widget.isVisible():
            table_proper_height -= table_container.meta_widget.height()
        if table_container.toolbar.isVisible():
            table_proper_height -= table_container.toolbar.height()
        if table_container.desc_widget.isVisible():
            table_proper_height -= table_container.desc_widget.height()
        return table_proper_height


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._pixmap = None

        self._layout = QVBoxLayout(self)
        self._stacked_layout = QStackedLayout()
        self.scrollarea = ScrollArea(self._app, self)
        self.table_container = self.scrollarea.t
        # TODO: collection container will be removed
        self.collection_container = CollectionContainer(self._app, self)
        self.bottom_panel = BottomPanel(app, self)

        self._setup_ui()

    def _setup_ui(self):
        self.scrollarea.setMinimumHeight(100)
        self.collection_container.hide()
        self._layout.addWidget(self.bottom_panel)
        self._layout.addLayout(self._stacked_layout)
        self._stacked_layout.addWidget(self.scrollarea)
        self._stacked_layout.addWidget(self.collection_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def show_model(self, model):
        self.set_body(self.scrollarea)
        # TODO: use PreemptiveTask
        aio.create_task(self.table_container.show_model(model))

    def show_songs(self, songs):
        self.collection_container.hide()
        self.set_body(self.scrollarea)
        self.table_container.show_songs(songs)

    def set_body(self, widget):
        self._stacked_layout.setCurrentWidget(widget)

    def show_collection(self, coll):

        def _show_pure_albums_coll(coll):
            self.set_body(self.scrollarea)
            reader = wrap(coll.models)
            self.table_container.show_albums_coll(reader)

        def _show_pure_songs_coll(coll):
            self.set_body(self.scrollarea)
            self.table_container.show_collection(coll)

        def _show_mixed_coll(coll):
            self.set_body(self.collection_container)
            self.collection_container.show_collection(coll)

        def _show_pure_videos_coll(coll):
            from feeluown.gui.page_containers.table import VideosRenderer

            self.set_body(self.scrollarea)
            reader = wrap(coll.models)
            renderer = VideosRenderer(reader)
            aio.create_task(self.table_container.set_renderer(renderer))

        if coll.type is CollectionType.sys_library:
            self._app.browser.goto(page='/colls/library')
            return

        types = set()
        for model in coll.models:
            types.add(model.meta.model_type)
            if len(types) >= 2:
                break

        if len(types) == 1:
            type_ = types.pop()
            if type_ == ModelType.song:
                _show_pure_songs_coll(coll)
            elif type_ == ModelType.album:
                _show_pure_albums_coll(coll)
            elif type_ == ModelType.video:
                _show_pure_videos_coll(coll)
            else:
                _show_mixed_coll(coll)
        else:
            _show_mixed_coll(coll)

    def show_background_image(self, pixmap):
        self._pixmap = pixmap
        if pixmap is None:
            self.table_container.meta_widget.setMinimumHeight(0)
        else:
            height = (self._app.height() - self.bottom_panel.height() -
                      self.table_container.toolbar.height()) // 2
            self.table_container.meta_widget.setMinimumHeight(height)
        self.update()

    def paintEvent(self, e):
        """
        draw pixmap as a the background with a dark overlay

        HELP: currently, this cost much CPU
        """
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # calculate available size
        draw_width = self.width()
        draw_height = 10  # spacing defined in table container
        draw_height += self.bottom_panel.height()
        if self.table_container.meta_widget.isVisible():
            draw_height += self.table_container.meta_widget.height()
        extra = self.table_container.current_extra
        if extra is not None and extra.isVisible():
            draw_height += extra.height()
        if self.table_container.toolbar.isVisible():
            draw_height += self.table_container.toolbar.height()

        scrolled = self.scrollarea.verticalScrollBar().value()
        max_scroll_height = draw_height - self.bottom_panel.height()

        if scrolled >= max_scroll_height:
            painter.save()
            painter.setBrush(self.palette().brush(QPalette.Window))
            painter.drawRect(self.bottom_panel.rect())
            painter.restore()
            return

        if self._pixmap is not None:
            self._draw_pixmap(painter, draw_width, draw_height, scrolled)
            self._draw_pixmap_overlay(painter, draw_width, draw_height, scrolled)
        else:
            # draw gradient for widgets(bottom panel + meta_widget + ...) above table
            self._draw_overlay(painter, draw_width, draw_height, scrolled)

            # if scrolled height > 30, draw background to seperate bottom_panel and body
            if scrolled >= 30:
                painter.save()
                painter.setBrush(self.palette().brush(QPalette.Window))
                painter.drawRect(self.bottom_panel.rect())
                painter.restore()
                return

            # since the body's background color is palette(base), we use
            # the color to draw background for remain empty area
            painter.save()
            painter.setBrush(self.palette().brush(QPalette.Base))
            painter.drawRect(0, draw_height, draw_width, self.height() - draw_height)
            painter.restore()
        painter.end()

    def _draw_pixmap_overlay(self, painter, draw_width, draw_height, scrolled):
        painter.save()
        rect = QRect(0, 0, draw_width, draw_height)
        painter.translate(0, -scrolled)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        color = self.palette().color(QPalette.Base)
        if draw_height == self.height():
            gradient.setColorAt(0, add_alpha(color, 180))
            gradient.setColorAt(1, add_alpha(color, 230))
        else:
            if self._app.theme_mgr.theme == Light:
                gradient.setColorAt(0, add_alpha(color, 220))
                gradient.setColorAt(0.1, add_alpha(color, 180))
                gradient.setColorAt(0.2, add_alpha(color, 140))
                gradient.setColorAt(0.6, add_alpha(color, 140))
                gradient.setColorAt(0.8, add_alpha(color, 200))
                gradient.setColorAt(0.9, add_alpha(color, 240))
                gradient.setColorAt(1, color)
            else:
                gradient.setColorAt(0, add_alpha(color, 50))
                gradient.setColorAt(0.6, add_alpha(color, 100))
                gradient.setColorAt(0.8, add_alpha(color, 200))
                gradient.setColorAt(0.9, add_alpha(color, 240))
                gradient.setColorAt(1, color)
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

    def _draw_overlay(self, painter, draw_width, draw_height, scrolled):
        painter.save()
        rect = QRect(0, 0, draw_width, draw_height)
        painter.translate(0, -scrolled)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, self.palette().color(QPalette.Window))
        gradient.setColorAt(1, self.palette().color(QPalette.Base))
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

    def _draw_pixmap(self, painter, draw_width, draw_height, scrolled):
        # scale pixmap
        scaled_pixmap = self._pixmap.scaledToWidth(
            draw_width,
            mode=Qt.SmoothTransformation)
        pixmap_size = scaled_pixmap.size()

        # draw the center part of the pixmap on available rect
        painter.save()
        brush = QBrush(scaled_pixmap)
        painter.setBrush(brush)
        # note: in practice, most of the time, we can't show the
        # whole artist pixmap, as a result, the artist head will be cut,
        # which causes bad visual effect. So we render the top-center part
        # of the pixmap here.
        y = (pixmap_size.height() - draw_height) // 3
        painter.translate(0, - y - scrolled)
        rect = QRect(0, y, draw_width, draw_height)
        painter.drawRect(rect)
        painter.restore()

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())
