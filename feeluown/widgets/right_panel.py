from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout
from feeluown.widgets.table_container import TableContainer


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.table_container = TableContainer(self._app, self)
        self._layout.addWidget(self.table_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(760, size.height())
