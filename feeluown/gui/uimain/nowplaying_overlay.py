from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QResizeEvent, QKeySequence
from PyQt5.QtWidgets import QWidget, QShortcut

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class NowplayingOverlay(QWidget):
    """
    TODO
    """

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.installEventFilter(self)

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)

        self.setStyleSheet('background: pink')

    def show(self):
        self.resize(self._app.size())
        super().show()

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            print('resize', event.size(), self.size())
            self.resize(event.size())
        return False
