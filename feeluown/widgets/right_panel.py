from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout
from feeluown.widgets.songs_table_container import SongsTableContainer


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.songs_table_container = SongsTableContainer(self._app, self)
        self._layout.addWidget(self.songs_table_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())
