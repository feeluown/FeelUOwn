from PyQt5.QtCore import Qt, QRect, QSize, QModelIndex
from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPalette
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea

from fuocore import aio
from fuocore.models import ModelType
from fuocore.reader import RandomSequentialReader

from feeluown.helpers import BgTransparentMixin
from feeluown.collection import DEFAULT_COLL_ALBUMS
from feeluown.containers.bottom_panel import BottomPanel
from feeluown.containers.table import TableContainer
from feeluown.containers.collection import CollectionContainer


def add_alpha(color, alpha):
    new_color = QColor(color)
    new_color.setAlpha(alpha)
    return new_color


class ScrollArea(QScrollArea, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self.t = TableContainer(app, self)
        self.setWidget(self.t)

        self.verticalScrollBar().valueChanged.connect(self.on_v_scrollbar_value_changed)

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


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._pixmap = None

        self._layout = QVBoxLayout(self)
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
        self._layout.addWidget(self.scrollarea)
        self._layout.addWidget(self.collection_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def show_model(self, model):
        self.scrollarea.show()
        self.collection_container.hide()
        # TODO: use PreemptiveTask
        aio.create_task(self.table_container.show_model(model))

    def show_songs(self, songs):
        self.collection_container.hide()
        self.scrollarea.show()
        self.table_container.show_songs(songs)

    def show_collection(self, coll):

        def _show_pure_albums_coll(coll):
            self.collection_container.hide()
            reader = RandomSequentialReader.from_list(coll.models)
            self.table_container.show_albums_coll(reader)

        def _show_pure_songs_coll(coll):
            self.collection_container.hide()
            self.scrollarea.show()
            self.table_container.show_collection(coll)

        def _show_mixed_coll(coll):
            self.scrollarea.hide()
            self.collection_container.show()
            self.collection_container.show_collection(coll)

        if coll.name == DEFAULT_COLL_ALBUMS:
            _show_pure_albums_coll(coll)
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
        if self._pixmap is None:
            return

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # calculate available size
        draw_width = self.width()
        draw_height = self.bottom_panel.height()
        if self.table_container.meta_widget.isVisible():
            draw_height += self.table_container.meta_widget.height()
        if self.table_container.toolbar.isVisible():
            draw_height += self.table_container.toolbar.height()

        scrolled = self.scrollarea.verticalScrollBar().value()
        max_scroll_height = draw_height - self.bottom_panel.height()
        if scrolled >= max_scroll_height:
            painter.save()
            painter.setBrush(self.palette().brush(QPalette.Window))
            painter.drawRect(self.rect())
            painter.restore()
            return

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

        # draw overlay
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        color = self.palette().color(QPalette.Base)
        if draw_height == self.height():
            gradient.setColorAt(0, add_alpha(color, 180))
            gradient.setColorAt(1, add_alpha(color, 230))
        else:
            gradient.setColorAt(0, add_alpha(color, 50))
            gradient.setColorAt(0.6, add_alpha(color, 100))
            gradient.setColorAt(0.8, add_alpha(color, 200))
            gradient.setColorAt(0.9, add_alpha(color, 240))
            gradient.setColorAt(1, color)
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

        painter.end()

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())
