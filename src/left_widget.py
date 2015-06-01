# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from widgets.playlist_widget import PlaylistWidget
from setting import ICON_PATH


class LeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_list_group = QGroupBox(u'创建的歌单')
        self.create_group_layout = QVBoxLayout()
        self.collection_list_group = QGroupBox(u'收藏的歌单')
        self.collection_group_layout = QVBoxLayout()

        self.create_list_widget = PlaylistWidget()
        self.collection_list_widget = PlaylistWidget()

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
        self.create_list_widget.setWordWrap(True)
        self.create_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)

        self.create_list_group.setLayout(self.create_group_layout)
        self.collection_list_group.setLayout(self.collection_group_layout)

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.create_group_layout.addWidget(self.create_list_widget)
        self.collection_group_layout.addWidget(self.collection_list_widget)

        self.layout.addWidget(self.create_list_group)
        self.layout.addWidget(self.collection_list_group)
        self.layout.addStretch(1)

