import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QAbstractItemView, QMenu

from feeluown.i18n import t
from feeluown.collection import CollectionType, Collection
from feeluown.gui.widgets.textlist import TextlistModel, TextlistView

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class CollectionListView(TextlistView):
    """
    Maybe make this a component instead of a widget.
    """

    show_collection = pyqtSignal([object])
    remove_collection = pyqtSignal([object])

    def __init__(self, app: "GuiApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setModel(CollectionListModel(self))

        self.clicked.connect(self._on_clicked)
        self._app.coll_mgr.scan_finished.connect(self.on_scan_finished)

    def on_scan_finished(self):
        model = self.model()
        assert isinstance(model, TextlistModel)
        model.clear()
        for coll in self._app.coll_mgr.listall():
            model.add(coll)

    def _on_clicked(self, index):
        collection = index.data(role=Qt.ItemDataRole.UserRole)
        self.show_collection.emit(collection)

    def contextMenuEvent(self, event):
        indexes = self.selectionModel().selectedIndexes()
        if len(indexes) != 1:
            return

        collection: Collection = self.model().data(indexes[0], Qt.ItemDataRole.UserRole)
        menu = QMenu()
        action = menu.addAction(t("remove-this-collection"))
        action.triggered.connect(lambda: self.remove_collection.emit(collection))
        menu.exec(event.globalPos())

    # dragEnterEvent -> dragMoveEvent -> dropEvent
    def dragEnterEvent(self, e):
        """
        Here we only check whether the dragged object this time is valid.
        If it is invalid, ignore this event.

        Then dropMoveEvent will not receive this event either.
        """
        mimedata = e.mimeData()
        if mimedata.hasFormat("fuo-model/x-song") or mimedata.hasFormat(
            "fuo-model/x-album"
        ):
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        """
        Because when moving the mouse, it may move to an area that is not
        a collection item, so here we check whether the model index at
        the current position meets the conditions.
        """
        # pylint: disable=all
        index = self.indexAt(e.position().toPoint())
        if index.isValid() and index.flags() & Qt.ItemFlag.ItemIsDropEnabled:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        mimedata = e.mimeData()
        model = mimedata.model
        index = self.indexAt(e.position().toPoint())
        coll = index.data(Qt.ItemDataRole.UserRole)
        self._results[index.row] = (index, None)
        self.viewport().update()
        is_success = coll.add(model)
        self._results[index.row] = (index, is_success)
        self.viewport().update()
        self._result_timer.start(2000)
        e.accept()


class CollectionListModel(TextlistModel):
    def flags(self, index):
        if not index.isValid():
            return 0
        flags = (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        return flags

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.ItemDataRole.DisplayRole:
            icon = "◎  "
            if item.type in (CollectionType.sys_library, CollectionType.sys_pool):
                icon = "◉  "
            return icon + item.name
        if role == Qt.ItemDataRole.ToolTipRole:
            return item.fpath
        return super().data(index, role)
