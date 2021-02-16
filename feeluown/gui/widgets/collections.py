import logging
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QAbstractItemView

from feeluown.collection import CollectionType
from .textlist import TextlistModel, TextlistView


logger = logging.getLogger(__name__)


class CollectionsModel(TextlistModel):
    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.DisplayRole:
            icon = '◎  '
            if item.type == CollectionType.sys_library:
                icon = '◉  '
            return icon + item.name
        if role == Qt.ToolTipRole:
            return item.fpath
        return super().data(index, role)


class CollectionsView(TextlistView):
    show_collection = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        collection = index.data(role=Qt.UserRole)
        self.show_collection.emit(collection)

    # dragEnterEvent -> dragMoveEvent -> dropEvent
    def dragEnterEvent(self, e):
        """
        在这里仅判断此次 drag 的对象是否有效，如果无效，则忽略这个事件。
        之后 dropMoveEvent 也就不会接收到这个事件。
        """
        mimedata = e.mimeData()
        if mimedata.hasFormat('fuo-model/x-song') or \
           mimedata.hasFormat('fuo-model/x-album'):
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        """
        由于鼠标移动时，可能会移动到非 collection item 的地方，
        所以在这里判断当前位置对应的 model index 是否符合条件。
        """
        # pylint: disable=all
        index = self.indexAt(e.pos())
        if index.isValid() and index.flags() & Qt.ItemIsDropEnabled:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        mimedata = e.mimeData()
        model = mimedata.model
        index = self.indexAt(e.pos())
        coll = index.data(Qt.UserRole)
        self._results[index.row] = (index, None)
        self.viewport().update()
        is_success = coll.add(model)
        self._results[index.row] = (index, is_success)
        self.viewport().update()
        self._result_timer.start(2000)
        e.accept()
