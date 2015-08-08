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
from constants import ICON_PATH
from left_widget import LeftWidget, LeftScrollArea
from right_widget import RightWidget
from top_widget import TopWidget


class UiMainWidget(object):
    """
    the main view
    """
    def setup_ui(self, MainWidget):
        self.status = QStatusBar()
        self.right_widget = RightWidget()
        self.left_widget = LeftScrollArea()
        self.top_widget = TopWidget()

        self.progress_info= QProgressBar()

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

        self.progress_info.setFixedHeight(2)
        self.progress_info.setTextVisible(False)

    def set_object_name(self):
        self.right_widget.setObjectName('right_widget')
        self.left_widget.setObjectName('left_widget')
        self.top_widget.setObjectName('top_widget')
        self.top_widget.search_edit.setObjectName('search_edit')
        self.progress_info.setObjectName('progress_info')

    def set_widgets_size(self):
        """
        set all widget specific size here, including child widget
        """
        self.left_widget.setFixedWidth(200)

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
        self.layout.addWidget(self.progress_info)
        self.set_layouts_prop()

    def set_layouts_prop(self):
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
