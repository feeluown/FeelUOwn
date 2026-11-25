import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView

from feeluown.gui.widgets.textlist import TextlistModel, TextlistView

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class SmartPlaylistListView(TextlistView):
    show_smart_playlist = pyqtSignal([object])

    def __init__(self, app: "GuiApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.setModel(SmartPlaylistListModel(self._app.smart_mgr, self))

        self.clicked.connect(self._on_clicked)
        self._app.smart_mgr.playlists_changed.connect(self.on_playlists_changed)
        self._app.smart_mgr.active_changed.connect(self.on_playlists_changed)

    def on_playlists_changed(self):
        model = self.model()
        assert isinstance(model, TextlistModel)
        model.clear()
        for playlist in self._app.smart_mgr.list_all():
            model.add(playlist)

    def _on_clicked(self, index):
        playlist = index.data(role=Qt.ItemDataRole.UserRole)
        self.show_smart_playlist.emit(playlist)


class SmartPlaylistListModel(TextlistModel):
    def __init__(self, smart_mgr, parent=None):
        super().__init__(parent)
        self._smart_mgr = smart_mgr

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.ItemDataRole.DisplayRole:
            prefix = "⚡ "
            try:
                active_id = self._smart_mgr.active_id
            except Exception:
                active_id = None
            marker = "● " if active_id is not None and item.id == active_id else ""
            return prefix + marker + item.name
        if role == Qt.ItemDataRole.ToolTipRole:
            return item.description or item.id
        return super().data(index, role)
