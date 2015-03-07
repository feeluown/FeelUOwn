# -*- coding=utf8 -*-
__author__ = 'cosven'

from PyQt4.QtGui import *
from PyQt4.QtCore import *


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
        self.last_music_btn = QPushButton(u"上一首")
        self.next_music_btn = QPushButton(u"下一首")
        self.play_pause_btn = QPushButton(u"播放")
        self.layout = QHBoxLayout()

        self.set_me()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

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
        self.music_table_widget = QTableWidget(0, 1)

        self.set_me()
        self.set_widgets_prop()
        self.set_widgets_size()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_size(self):
        pass

    def set_widgets_prop(self):
        self.music_table_widget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.music_table_widget.setHorizontalHeaderLabels([u'歌曲名'])

    def set_layouts_prop(self):
        self.layout.addWidget(self.music_table_widget)


class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.info_widget = InfoWidget()
        self.user_widget = UserWidget()
        self.play_widget = PlayWidget()
        self.info_layout = QVBoxLayout()
        self.user_layout = QVBoxLayout()
        self.play_layout = QHBoxLayout()
        self.top_container = QHBoxLayout()
        self.bottom_container = QHBoxLayout()
        self.layout = QVBoxLayout()

        self.set_me()
        self.set_widgets_size()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)
        self.resize(800, 480)

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
