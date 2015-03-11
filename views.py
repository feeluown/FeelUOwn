# -*- coding=utf8 -*-
__author__ = 'cosven'

"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *


from higherapi import User


class UserWidget(QWidget):
    def __init__(self):
        super(UserWidget, self).__init__()
        self.text_label = QLabel(u'用戶名')
        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.text_label.setAlignment(Qt.AlignCenter)

    def set_layouts_prop(self):
        self.layout.addWidget(self.text_label)


class PlayWidget(QWidget):
    def __init__(self):
        super(PlayWidget, self).__init__()
        self.last_music_btn = QPushButton()
        self.next_music_btn = QPushButton()
        self.play_pause_btn = QPushButton()
        self.layout = QHBoxLayout()

        self.set_me()
        self.set_layouts_prop()
        self.set_widgets_prop()
        self.set_widgets_size()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.play_pause_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay))
        self.last_music_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.next_music_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipForward))

    def set_widgets_size(self):
        pass

    def set_layouts_prop(self):
        self.layout.addWidget(self.last_music_btn)
        self.layout.addWidget(self.play_pause_btn)
        self.layout.addWidget(self.next_music_btn)


class InfoWidget(QWidget):
    def __init__(self):
        super(InfoWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.music_table_widget = QTableWidget(1, 1)

        self.set_me()
        self.set_widgets_prop()
        self.set_widgets_size()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_size(self):
        pass

    def set_widgets_prop(self):
        self.music_table_widget.horizontalHeader().setResizeMode(
            0, QHeaderView.Stretch)
        self.music_table_widget.setHorizontalHeaderLabels([u'歌曲名'])
        self.music_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)

    def set_layouts_prop(self):
        self.layout.addWidget(self.music_table_widget)


class UiMainWidget(object):
    """
    the main view
    """
    def setup_ui(self, MainWidget):
        self.info_widget = InfoWidget()
        self.user_widget = UserWidget()
        self.play_widget = PlayWidget()
        self.info_layout = QVBoxLayout()
        self.user_layout = QVBoxLayout()
        self.play_layout = QHBoxLayout()
        self.top_container = QHBoxLayout()
        self.bottom_container = QHBoxLayout()
        self.layout = QVBoxLayout(MainWidget)
        self.user = User()

        self.set_widgets_size()
        self.set_layouts_prop()

    def set_widgets_size(self):
        self.play_widget.setFixedHeight(100)
        self.user_widget.setFixedWidth(200)

    def set_layouts_prop(self):
        self.info_layout.addWidget(self.info_widget)
        self.user_layout.addWidget(self.user_widget)
        self.play_layout.addWidget(self.play_widget)
        self.top_container.addLayout(self.user_layout)
        self.top_container.addLayout(self.info_layout)
        self.bottom_container.addLayout(self.play_layout)
        self.layout.addLayout(self.top_container)
        self.layout.addLayout(self.bottom_container)