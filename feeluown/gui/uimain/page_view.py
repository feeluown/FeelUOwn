import logging
import sys

from PyQt5.QtCore import Qt, QRect, QSize, QEasingCurve, QEvent
from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPalette
from PyQt5.QtWidgets import QAbstractScrollArea, QFrame, QVBoxLayout, QStackedLayout

from feeluown.utils import aio
from feeluown.library import ModelType
from feeluown.utils.reader import wrap

from feeluown.gui.theme import Light
from feeluown.gui.helpers import BgTransparentMixin, BaseScrollAreaForNoScrollItemView
from feeluown.gui.uimain.toolbar import BottomPanel
from feeluown.gui.page_containers.table import TableContainer
from feeluown.gui.base_renderer import VFillableBg

logger = logging.getLogger(__name__)


def add_alpha(color, alpha):
    new_color = QColor(color)
    new_color.setAlpha(alpha)
    return new_color


class ScrollArea(BaseScrollAreaForNoScrollItemView, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self.t = TableContainer(app, self)
        self.setWidget(self.t)
        #: widgets that may affect the itemview height
        self._other_widgets = [self.t.meta_widget, self.t.toolbar]
        for w in self._other_widgets:
            w.installEventFilter(self)

        # As far as I know, KDE and GNOME can't auto hide the scrollbar,
        # and they show an old-fation vertical scrollbar.
        # HELP: implement an auto-hide scrollbar for Linux
        if sys.platform.lower() != 'darwin':
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def get_itemview(self):
        return self.t.current_table

    def height_for_itemview(self):
        height = self.height()
        for w in self._other_widgets:
            if w.isVisible():
                height -= w.height()
        return height

    def eventFilter(self, _, event):
        if event.type() == QEvent.Resize:
            self.maybe_resize_itemview()
        return False

    def fillable_bg_height(self):
        """Implement VFillableBg protocol"""
        height = 0
        table_container = self.t
        if table_container.meta_widget.isVisible():
            height += table_container.meta_widget.height()
        extra = table_container.current_extra
        if extra is not None and extra.isVisible():
            height += extra.height()
        if table_container.toolbar.isVisible():
            height += table_container.toolbar.height()
        return height


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._pixmap = None

        self._layout = QVBoxLayout(self)
        self._stacked_layout = QStackedLayout()
        self.scrollarea = ScrollArea(self._app, self)
        self.table_container = self.scrollarea.t
        self.bottom_panel = BottomPanel(app, self)

        self._setup_ui()

    def _setup_ui(self):
        self.scrollarea.setMinimumHeight(100)
        self._layout.addWidget(self.bottom_panel)
        self._layout.addLayout(self._stacked_layout)
        self._stacked_layout.addWidget(self.scrollarea)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def show_songs(self, songs):
        self.set_body(self.scrollarea)
        self.table_container.show_songs(songs)

    def set_body(self, widget):
        """

        .. versionadded:: 3.7.7
        """
        if widget is self.table_container:
            widget = self.scrollarea

        if widget is not self.scrollarea:
            self.show_background_image(None)

        # remove tmp widgets
        for i in range(self._stacked_layout.count()):
            w = self._stacked_layout.widget(i)
            if w not in (self.scrollarea, ):
                self._stacked_layout.removeWidget(w)

        widget.installEventFilter(self)
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().installEventFilter(self)

        self._stacked_layout.addWidget(widget)
        self._stacked_layout.setCurrentWidget(widget)

    def eventFilter(self, _, event):
        # Refresh when the body is scrolled.
        if event.type() == QEvent.Wheel:
            self.update()
        return False

    def show_collection(self, coll, model_type):

        def _show_pure_albums_coll(coll):
            self.set_body(self.scrollarea)
            reader = wrap(coll.models)
            self.table_container.show_albums_coll(reader)

        def _show_pure_songs_coll(coll):
            self.set_body(self.scrollarea)
            self.table_container.show_collection(coll)

        def _show_pure_videos_coll(coll):
            from feeluown.gui.page_containers.table import VideosRenderer

            self.set_body(self.scrollarea)
            reader = wrap(coll.models)
            renderer = VideosRenderer(reader)
            aio.create_task(self.table_container.set_renderer(renderer))

        if model_type == ModelType.song:
            _show_pure_songs_coll(coll)
        elif model_type == ModelType.album:
            _show_pure_albums_coll(coll)
        elif model_type == ModelType.video:
            _show_pure_videos_coll(coll)
        else:
            logger.warning("can't render this kind of collection")

    def show_background_image(self, pixmap):
        self._pixmap = pixmap
        self._adjust_meta_widget_height()
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
        draw_height = self.bottom_panel.height()
        current_widget = self._stacked_layout.currentWidget()
        if isinstance(current_widget, VFillableBg):
            draw_height += current_widget.fillable_bg_height()

        widget = self._stacked_layout.currentWidget()
        if isinstance(widget, QAbstractScrollArea):
            scrolled = widget.verticalScrollBar().value()
        else:
            scrolled = 0
        max_scroll_height = draw_height - self.bottom_panel.height()

        # Draw the whole background with QPalette.Base color.
        painter.save()
        painter.setBrush(self.palette().brush(QPalette.Base))
        painter.drawRect(self.rect())
        painter.restore()

        # Do not draw the pixmap or overlay when it scrolled a lot.
        if scrolled > max_scroll_height:
            painter.save()
            painter.setBrush(self.palette().brush(QPalette.Window))
            painter.drawRect(self.bottom_panel.rect())
            painter.restore()
            return

        if self._pixmap is not None:
            self._draw_pixmap(painter, draw_width, draw_height, scrolled)
            self._draw_pixmap_overlay(painter, draw_width, draw_height, scrolled)
            curve = QEasingCurve(QEasingCurve.OutCubic)
            if max_scroll_height == 0:
                alpha_ratio = 1.0
            else:
                alpha_ratio = min(scrolled / max_scroll_height, 1.0)
            alpha = int(250 * curve.valueForProgress(alpha_ratio))
            painter.save()
            color = self.palette().color(QPalette.Window)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.drawRect(self.bottom_panel.rect())
            painter.restore()
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
        assert self._pixmap is not None
        pixmap_size = self._pixmap.size()

        # draw the center part of the pixmap on available rect
        painter.save()
        if pixmap_size.width() / draw_width * draw_height >= pixmap_size.height():
            scaled_pixmap = self._pixmap.scaledToHeight(
                draw_height,
                mode=Qt.SmoothTransformation)
            brush = QBrush(scaled_pixmap)
            painter.setBrush(brush)
            pixmap_size = scaled_pixmap.size()
            x = (pixmap_size.width() - draw_width) // 2
            painter.translate(-x, -scrolled)
            rect = QRect(0, 0, pixmap_size.width(), draw_height)
        else:
            scaled_pixmap = self._pixmap.scaledToWidth(
                draw_width,
                mode=Qt.SmoothTransformation)
            pixmap_size = scaled_pixmap.size()
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
        return QSize(660, size.height())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._pixmap is not None and e.oldSize().width() != e.size().width():
            self._adjust_meta_widget_height()

    def _adjust_meta_widget_height(self):
        # HACK: adjust height of table_container's meta_widget to
        # adapt to background image.
        if self._pixmap is None:
            self.table_container.meta_widget.setMinimumHeight(0)
        else:
            height = (self._background_image_height_hint() -
                      self.bottom_panel.height() -
                      self.table_container.toolbar.height())
            self.table_container.meta_widget.setMinimumHeight(height)

    def _background_image_height_hint(self):
        return self.width() * 5 // 9
