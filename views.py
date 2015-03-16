# -*- coding=utf8 -*-
__author__ = 'cosven'

"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from PyQt4.phonon import Phonon


class UserWidget(QWidget):
    def __init__(self, parent=None):
        super(UserWidget, self).__init__(parent)
        self.login_btn = QPushButton(u'网易通行证登陆')
        self.text_label = QLabel(u'歌曲列表')
        self.test_btn = QPushButton()
        self.list_widget = QListWidget()
        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.text_label.setAlignment(Qt.AlignLeft)
        self.test_btn.setText(u'使用测试账号')

    def set_layouts_prop(self):
        self.layout.addWidget(self.text_label)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.test_btn)


class PlayWidget(QWidget):
    def __init__(self, parent=None):
        super(PlayWidget, self).__init__(parent)
        self.last_music_btn = QPushButton()
        self.next_music_btn = QPushButton()
        self.play_pause_btn = QPushButton()
        self.text_label = QLabel()
        self.time_lcd = QLCDNumber()
        self.seek_slider = Phonon.SeekSlider(self)
        self.layout = QHBoxLayout()

        self.set_me()
        self.set_widgets_prop()
        self.set_layouts_prop()

    def paintEvent(self, QPaintEvent):
        """
        If you subclass a custom widget from QWidget,
        then in order to use the StyleSheets you need to provide a paintEvent to the custom widget :

        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """

        option = QStyleOption()
        option.init(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_me(self):
        # it will conflict with stylesheet, stylesheet has the priority
        # by default, autofill background with Qpalette.Window color(system color)
        self.setAutoFillBackground(True)

        self.setProperty('class', 'QWidget')
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.play_pause_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay))
        self.last_music_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.next_music_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.time_lcd.display('00:00')

    def set_layouts_prop(self):
        self.layout.addWidget(self.last_music_btn)
        self.layout.addWidget(self.play_pause_btn)
        self.layout.addWidget(self.next_music_btn)
        self.layout.addWidget(self.text_label)
        self.layout.addWidget(self.seek_slider)
        self.layout.addWidget(self.time_lcd)


class InfoWidget(QWidget):
    def __init__(self, parent=None):
        super(InfoWidget, self).__init__(None)
        self.layout = QVBoxLayout()
        self.music_table_widget = QTableWidget(1, 1)

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
        option.init(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

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
        self.show_container = QHBoxLayout()
        self.control_container = QHBoxLayout()
        self.layout = QVBoxLayout(MainWidget)

        self.set_widgets_prop()
        self.set_widgets_size()
        self.set_layouts_prop()

    def set_widgets_prop(self):
        self.info_widget.setObjectName('info_widget')
        self.user_widget.setObjectName('user_widget')
        self.play_widget.setObjectName('play_widget')

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.init(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_widgets_size(self):
        """
        set all widget specific size here, including child widget
        """
        self.play_widget.setFixedHeight(100)
        self.user_widget.setFixedWidth(200)

    def set_layouts_prop(self):
        self.info_layout.addWidget(self.info_widget)
        self.user_layout.addWidget(self.user_widget)
        self.play_layout.addWidget(self.play_widget)
        self.show_container.addLayout(self.user_layout)
        self.show_container.addLayout(self.info_layout)
        self.control_container.addLayout(self.play_layout)
        self.layout.addLayout(self.control_container)
        self.layout.addLayout(self.show_container)

        self.layout.setContentsMargins(0,0,0,0)
