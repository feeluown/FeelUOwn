# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from constants import ICON_PATH
from widgets.playlist_widget import SpreadWidget, RecommendItem


class LeftScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.central_widget = LeftWidget()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.set_widgets_prop()

    def set_widgets_prop(self):
        self.setWidgetResizable(True)
        self.ensureWidgetVisible(self.central_widget)
        self.setWidget(self.central_widget)
        self.central_widget.setFixedWidth(200)


class LeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_title_layout = QHBoxLayout()
        self.collection_title_layout = QHBoxLayout()
        self.local_title_layout = QHBoxLayout()

        self.recommend_title = QLabel(u'推荐')
        self.create_title = QLabel(u'创建的歌单')
        self.collection_title = QLabel(u'收藏的歌单')
        self.local_title = QLabel(u'本地歌单')

        self.create_fold_spread_btn = QPushButton()
        self.collection_fold_spread_btn = QPushButton()
        self.local_fold_spread_btn = QPushButton()

        self.new_playlist_btn = QPushButton('+')

        self.recommend_list_widget = SpreadWidget()
        self.create_list_widget = SpreadWidget()
        self.collection_list_widget = SpreadWidget()
        self.local_list_widget = SpreadWidget()

        self.fm_item = RecommendItem(self.recommend_list_widget, "私人FM", 
                                     QPixmap(ICON_PATH + 'fm.png'))

        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_me(self):
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

    def set_objects_name(self):
        self.setObjectName('left_widget')
        self.create_title.setObjectName('title')
        self.collection_title.setObjectName('title')
        self.local_title.setObjectName('title')
        self.recommend_title.setObjectName('title')

        self.create_fold_spread_btn.setObjectName('playlist_fold_spread')
        self.collection_fold_spread_btn.setObjectName('playlist_fold_spread')
        self.local_fold_spread_btn.setObjectName('playlist_fold_spread')

        self.new_playlist_btn.setObjectName('new_playlist_btn')

    def set_widgets_prop(self):
        self.set_objects_name()

        self.create_fold_spread_btn.setCheckable(True)
        self.collection_fold_spread_btn.setCheckable(True)
        self.local_fold_spread_btn.setCheckable(True)

        self.create_fold_spread_btn.setFixedSize(24, 24)
        self.collection_fold_spread_btn.setFixedSize(24, 24)
        self.local_fold_spread_btn.setFixedSize(24, 24)

    def set_layouts_prop(self):

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.recommend_list_widget.layout().addWidget(self.fm_item)

        self.create_title_layout.addWidget(self.create_title)
        self.create_title_layout.addStretch(1)
        self.create_title_layout.addWidget(self.new_playlist_btn)
        self.create_title_layout.addSpacing(3)
        self.create_title_layout.addWidget(self.create_fold_spread_btn)
        self.create_title_layout.addSpacing(10)
        self.collection_title_layout.addWidget(self.collection_title)
        self.collection_title_layout.addWidget(self.collection_fold_spread_btn)
        self.collection_title_layout.addSpacing(10)
        self.local_title_layout.addWidget(self.local_title)
        self.local_title_layout.addWidget(self.local_fold_spread_btn)
        self.local_title_layout.addSpacing(10)

        self.layout.addWidget(self.recommend_title)
        self.layout.addWidget(self.recommend_list_widget)
        self.layout.addLayout(self.create_title_layout)
        self.layout.addWidget(self.create_list_widget)
        self.layout.addLayout(self.collection_title_layout)
        self.layout.addWidget(self.collection_list_widget)
        # self.layout.addLayout(self.local_title_layout)
        # self.layout.addWidget(self.local_list_widget)

        self.layout.addStretch(1)
