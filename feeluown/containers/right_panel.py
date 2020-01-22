from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea

from fuocore.models import ModelType
from fuocore.reader import RandomSequentialReader

from feeluown.collection import DEFAULT_COLL_ALBUMS
from feeluown.containers.bottom_panel import BottomPanel
from feeluown.containers.table import TableContainer
from feeluown.containers.collection import CollectionContainer

from fuocore import aio


class ScrollArea(QScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self.t = TableContainer(app, self)
        self.setWidget(self.t)


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._pixmap = None

        self._layout = QVBoxLayout(self)
        self.scrollarea = ScrollArea(self._app, self)
        self.table_container = self.scrollarea.t
        self.collection_container = CollectionContainer(self._app, self)
        self.bottom_panel = BottomPanel(app, self)
        self.setup_ui()

    def setup_ui(self):
        self.scrollarea.setMinimumHeight(100)
        self.collection_container.hide()
        self._layout.addWidget(self.bottom_panel)
        self._layout.addWidget(self.scrollarea)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())

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
        pure_songs = True
        for model in coll.models:
            if model.meta.model_type != ModelType.song:
                pure_songs = False
                break

        if coll.name == DEFAULT_COLL_ALBUMS:
            self.collection_container.hide()
            reader = RandomSequentialReader.from_list(coll.models)
            self.table_container.show_albums_coll(reader)
            return

        if pure_songs:
            self.collection_container.hide()
            self.scrollarea.show()
            self.table_container.show_collection(coll)
        else:
            self.scrollarea.hide()
            self.collection_container.show()
            self.collection_container.show_collection(coll)

    # draw background cover
    def show_background_image(self, pixmap):
        self._pixmap = pixmap
        if pixmap is None:
            self.table_container.meta_widget.setMinimumHeight(0)
        else:
            height = (self._app.height() - self.bottom_panel.height()) // 2
            self.table_container.meta_widget.setMinimumHeight(height)
        self.update()

    def paintEvent(self, e):
        if self._pixmap is None:
            return

        draw_height = self.bottom_panel.height()
        if self.table_container.meta_widget.isVisible():
            draw_height += self.table_container.meta_widget.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        scaled_pixmap = self._pixmap.scaledToWidth(
            self.width(),
            mode=Qt.SmoothTransformation
        )
        pixmap_size = scaled_pixmap.size()
        painter.save()
        brush = QBrush(scaled_pixmap)
        painter.setBrush(brush)
        y = (pixmap_size.height() - draw_height) // 2
        painter.translate(0, -y)
        rect = QRect(0, y, self.width(), draw_height)
        painter.drawRect(rect)
        painter.restore()

        painter.save()
        # draw overlay
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 200))
        painter.drawRect(self.rect())
        painter.restore()
        painter.end()
