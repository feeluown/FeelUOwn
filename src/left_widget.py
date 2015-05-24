# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from widgets.music_table_widget import MusicTableWidget
from setting import ICON_PATH


class LeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = QListWidget()
        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.list_widget.setWordWrap(True)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.list_widget)

