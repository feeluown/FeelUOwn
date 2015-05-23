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
from left_widget import LeftWidget
from right_widget import RightWidget
from top_widget import TopWidget


class UiMainWidget(object):
    """
    the main view
    """
    def setup_ui(self, MainWidget):
        self.status = QStatusBar()
        self.info_widget = RightWidget()
        self.user_widget = LeftWidget()
        self.play_widget = TopWidget()
        self.info_layout = QVBoxLayout()
        self.user_layout = QVBoxLayout()
        self.play_layout = QHBoxLayout()
        self.show_container = QHBoxLayout()
        self.control_container = QHBoxLayout()
        self.layout = QVBoxLayout(MainWidget)

        self.set_widgets_prop()
        self.set_layouts_prop()

    def set_widgets_prop(self):
        self.set_widgets_size()
        self.set_object_name()

    def set_object_name(self):
        self.info_widget.setObjectName('info_widget')
        self.user_widget.setObjectName('user_widget')
        self.play_widget.setObjectName('play_widget')
        self.play_widget.search_edit.setObjectName('search_edit')
        self.play_widget.search_btn.setObjectName('search_btn')

    def set_widgets_size(self):
        """
        set all widget specific size here, including child widget
        """
        self.play_widget.setFixedHeight(80)
        self.user_widget.setMaximumWidth(220)

    def set_layouts(self):
        self.info_layout.addWidget(self.info_widget)
        self.user_layout.addWidget(self.user_widget)
        self.play_layout.addWidget(self.play_widget)
        self.show_container.addLayout(self.user_layout)
        self.show_container.addLayout(self.info_layout)
        self.control_container.addLayout(self.play_layout)
        self.layout.addLayout(self.control_container)
        self.layout.addLayout(self.show_container)
        self.layout.addWidget(self.status)

        self.set_layouts_prop()

    def set_layouts_prop(self):
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)
