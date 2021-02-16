from PyQt5.QtCore import Qt, pyqtSignal

from .imglist import (
    ImgListModel, ImgListDelegate, ImgListView,
    ImgFilterProxyModel
)


class PlaylistListModel(ImgListModel):
    pass


class PlaylistListDelegate(ImgListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False


class PlaylistFilterProxyModel(ImgFilterProxyModel):
    pass


class PlaylistListView(ImgListView):
    show_playlist_needed = pyqtSignal([object])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        delegate = PlaylistListDelegate(self)
        self.setItemDelegate(delegate)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        artist = index.data(Qt.UserRole)
        self.show_playlist_needed.emit(artist)
