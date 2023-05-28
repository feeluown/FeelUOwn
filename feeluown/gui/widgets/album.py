from PyQt5.QtCore import Qt, pyqtSignal

from feeluown.library import AlbumModel
from feeluown.models import AlbumType
from .imglist import (
    ImgListModel, ImgListDelegate, ImgListView,
    ImgFilterProxyModel
)


class AlbumListModel(ImgListModel):
    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None

        album = self._items[offset]
        if role == Qt.WhatsThisRole:
            if isinstance(album, AlbumModel):
                if album.song_count >= 0:
                    # Like: 1991-01-01 10首
                    return f'{album.released} {album.song_count}首'
                return album.released
        return super().data(index, role)


class AlbumListDelegate(ImgListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False


class AlbumFilterProxyModel(ImgFilterProxyModel):
    def __init__(self, parent=None, types=None):
        super().__init__(parent)

        self.types = types

    def filter_by_types(self, types):
        # if types is a empty list or None, we show all albums
        if not types:
            types = None
        self.types = types
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        accepted = super().filterAcceptsRow(source_row, source_parent)
        source_model = self.sourceModel()
        assert isinstance(source_model, AlbumListModel)
        index = source_model.index(source_row, parent=source_parent)
        album = index.data(Qt.UserRole)
        if accepted and self.types:
            accepted = AlbumType(album.type_) in self.types
        return accepted


class AlbumListView(ImgListView):
    show_album_needed = pyqtSignal([object])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        delegate = AlbumListDelegate(self)
        self.setItemDelegate(delegate)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        album = index.data(Qt.UserRole)
        self.show_album_needed.emit(album)
