from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout

from fuocore.models import ModelType
from fuocore.reader import RandomSequentialReader

from feeluown.collection import DEFAULT_COLL_ALBUMS
from feeluown.widgets.table_container import TableContainer
from feeluown.widgets.collection_container import CollectionContainer

from fuocore import aio


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.table_container = TableContainer(self._app, self)
        self.collection_container = CollectionContainer(self._app, self)
        self.table_container.hide()
        self.collection_container.hide()
        self._layout.addWidget(self.table_container)
        self._layout.addWidget(self.collection_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())

    def show_model(self, model):
        self.table_container.show()
        self.collection_container.hide()
        # TODO: use PreemptiveTask
        aio.create_task(self.table_container.show_model(model))

    def show_songs(self, songs):
        self.collection_container.hide()
        self.songs_table_container.show_songs(songs)

    def show_collection(self, coll):
        pure_songs = True
        for model in coll.models:
            if model.meta.model_type != ModelType.song:
                pure_songs = False
                break

        if coll.name == DEFAULT_COLL_ALBUMS:
            self.collection_container.hide()
            reader = RandomSequentialReader.from_list(coll.models)
            self.table_container.show_albums(reader)
            return

        if pure_songs:
            self.collection_container.hide()
            self.table_container.show()
            self.table_container.show_collection(coll)
        else:
            self.table_container.hide()
            self.collection_container.show()
            self.collection_container.show_collection(coll)
