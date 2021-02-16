from PyQt5.QtCore import Qt, pyqtSignal

from .imglist import (
    ImgListModel, ImgListDelegate, ImgListView,
    ImgFilterProxyModel
)


class ArtistListModel(ImgListModel):
    pass


class ArtistListDelegate(ImgListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = True


class ArtistFilterProxyModel(ImgFilterProxyModel):
    pass


class ArtistListView(ImgListView):
    show_artist_needed = pyqtSignal([object])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        delegate = ArtistListDelegate(self)
        self.setItemDelegate(delegate)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        artist = index.data(Qt.UserRole)
        self.show_artist_needed.emit(artist)
