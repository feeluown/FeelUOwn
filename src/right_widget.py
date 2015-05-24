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


class RightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.music_table_widget = MusicTableWidget()
        self.current_playing_widget = MusicTableWidget()
        self.music_search_widget = MusicTableWidget()

        self.set_me()
        self.set_widgets_prop()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

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

    def set_widgets_prop(self):
        pass

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.music_search_widget)
        self.layout.addWidget(self.music_table_widget)
        self.layout.addWidget(self.current_playing_widget)
