from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFrame, QSizePolicy, QVBoxLayout


from feeluown.widgets.meta import CollMetaWidget
from feeluown.widgets.song_list import SongListView


class CollectionBody(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.meta_widget = CollMetaWidget(self)
        self.song_list_view = SongListView(self)

        self._layout = QVBoxLayout(self)
        self._setup_ui()

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(300, size.height())

    def _setup_ui(self):

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.song_list_view)
