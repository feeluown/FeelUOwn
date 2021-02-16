from PyQt5.QtCore import Qt, pyqtSignal

from .imglist import (
    ImgListModel, ImgListDelegate, ImgListView,
    ImgFilterProxyModel
)


class VideoListModel(ImgListModel):
    def data(self, index, role):
        offset = index.row()
        if not index.isValid() or offset >= len(self._items):
            return None
        video = self._items[offset]
        if role == Qt.DisplayRole:
            return video.title_display
        return super().data(index, role)


class VideoListDelegate(ImgListDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.as_circle = False
        self.w_h_ratio = 1.618


class VideoFilterProxyModel(ImgFilterProxyModel):
    pass


class VideoListView(ImgListView):
    play_video_needed = pyqtSignal([object])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        delegate = VideoListDelegate(self)
        self.setItemDelegate(delegate)

        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        video = index.data(Qt.UserRole)
        self.play_video_needed.emit(video)
