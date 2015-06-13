# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from setting import ICON_PATH
from widgets.playlist_widget import PlaylistWidget, PlaylistItem



class LeftScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.central_widget = LeftWidget()

        self.set_widgets_prop()

    def set_widgets_prop(self):
        self.setWidgetResizable(True)
        self.ensureWidgetVisible(self.central_widget)
        self.setWidget(self.central_widget)
        self.central_widget.setFixedWidth(200)


class LeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_title = QLabel(u'创建的歌单')
        self.collection_title = QLabel(u'收藏的歌单')
        self.local_title = QLabel(u'本地歌单')

        self.create_list_widget = PlaylistWidget()
        self.collection_list_widget = PlaylistWidget()
        self.local_list_widget = PlaylistWidget()

        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def paintEvent(self, QPaintEvent):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_me(self):
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

    def set_objects_name(self):
        self.setObjectName('left_widget')
        self.create_title.setObjectName('title')
        self.collection_title.setObjectName('title')
        self.local_title.setObjectName('title')

    def set_widgets_prop(self):
        self.set_objects_name()

    def set_layouts_prop(self):

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.create_title)
        self.layout.addWidget(self.create_list_widget)
        self.layout.addWidget(self.collection_title)
        self.layout.addWidget(self.collection_list_widget)
        self.layout.addWidget(self.local_title)
        self.layout.addWidget(self.local_list_widget)

        self.layout.addStretch(1)