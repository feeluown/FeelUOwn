# -*- coding=utf8 -*-


"""
ui design

every basic widget class has three public \
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
        self.right_widget = RightWidget()
        self.left_widget = LeftWidget()
        self.top_widget = TopWidget()
        self.right_layout = QVBoxLayout()
        self.left_layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.show_container = QHBoxLayout()
        self.control_container = QHBoxLayout()
        self.layout = QVBoxLayout(MainWidget)

        self.set_widgets()
        self.set_layouts()

    def set_widgets(self):
        self.set_widgets_size()
        self.set_object_name()

    def set_object_name(self):
        self.right_widget.setObjectName('right_widget')
        self.left_widget.setObjectName('left_widget')
        self.top_widget.setObjectName('top_widget')
        self.top_widget.search_edit.setObjectName('search_edit')
        self.top_widget.search_btn.setObjectName('search_btn')

    def set_widgets_size(self):
        """
        set all widget specific size here, including child widget
        """
        self.top_widget.setFixedHeight(80)
        self.left_widget.setMaximumWidth(220)

    def set_layouts(self):
        self.right_layout.addWidget(self.right_widget)
        self.left_layout.addWidget(self.left_widget)
        self.top_layout.addWidget(self.top_widget)
        self.show_container.addLayout(self.left_layout)
        self.show_container.addLayout(self.right_layout)
        self.control_container.addLayout(self.top_layout)
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
