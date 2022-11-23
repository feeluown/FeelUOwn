import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QFrame

from feeluown.gui.helpers import BgTransparentMixin


class ScrollArea(QScrollArea, BgTransparentMixin):
    """
    ScrollArea is designed to be used as a container for page_body.
    Be careful when you use it as a container for other widgets.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        if sys.platform.lower() != 'darwin':
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
