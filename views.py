# -*- coding=utf8 -*-
__author__ = 'cosven'

"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from PyQt4.phonon import Phonon


class UserWidget(QWidget):
    def __init__(self, parent=None):
        super(UserWidget, self).__init__(parent)
        self.text_label = QLabel(u'歌曲列表')
        self.list_widget = QListWidget()
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
        option.init(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.text_label.setObjectName('playlist_title')
        self.list_widget.setWordWrap(True)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_label.setAlignment(Qt.AlignLeft)

    def set_layouts_prop(self):
        self.layout.addWidget(self.text_label)
        self.layout.addWidget(self.list_widget)


class PlayWidget(QWidget):
    def __init__(self, parent=None):
        super(PlayWidget, self).__init__(parent)
        self.last_music_btn = QPushButton()
        self.next_music_btn = QPushButton()
        self.play_pause_btn = QPushButton()
        self.text_label = QLabel()
        self.img_label = QLabel()
        self.time_lcd = QLabel()
        self.seek_slider = Phonon.SeekSlider(self)
        self.search_edit = QLineEdit()
        self.search_btn = QPushButton()
        self.show_current_list = QPushButton()
        self.login_btn = QPushButton()
        self.help_btn = QPushButton()
        self.edit_layout = QHBoxLayout()
        self.center_layout = QHBoxLayout()
        self.center_layout_l = QVBoxLayout()
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
        # self.setAutoFillBackground(True)
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.login_btn.setIconSize(QSize(40, 40))
        self.play_pause_btn.setIconSize(QSize(40, 40))
        self.last_music_btn.setIconSize(QSize(40, 40))
        self.next_music_btn.setIconSize(QSize(40, 40))
        self.help_btn.setIconSize(QSize(25, 25))
        self.show_current_list.setIconSize(QSize(25, 25))
        self.show_current_list.setToolTip(u'正在播放列表')
        self.login_btn.setToolTip(u'登录')
        self.login_btn.setIcon(QIcon('icons/login_hover.png'))
        self.play_pause_btn.setIcon(QIcon('icons/pause_hover.png'))
        self.last_music_btn.setIcon(QIcon('icons/last_hover.png'))
        self.next_music_btn.setIcon(QIcon('icons/next_hover.png'))
        self.show_current_list.setIcon(QIcon('icons/current_play.png'))
        self.help_btn.setIcon(QIcon('icons/help.png'))

        self.login_btn.setFixedSize(40, 40)

        self.play_pause_btn.setObjectName('play_pause')
        self.last_music_btn.setObjectName('last')
        self.next_music_btn.setObjectName('next')
        self.login_btn.setObjectName('login_btn')

        self.text_label.setText(u'未播放任何歌曲')
        self.text_label.setObjectName(u'music_title')
        self.text_label.setAlignment(Qt.AlignCenter)
        self.img_label.setFixedSize(40, 40)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.seek_slider.setFixedWidth(500)
        self.time_lcd.setText('00:00')
        # self.search_btn.setText(u'搜索')
        self.search_edit.setFixedHeight(25)
        self.search_btn.setFixedSize(25, 25)
        self.search_edit.setPlaceholderText(u'搜索单曲')

    def set_layouts_prop(self):
        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.last_music_btn)
        self.layout.addWidget(self.play_pause_btn)
        self.layout.addWidget(self.next_music_btn)
        self.layout.addStretch(1)
        self.center_layout.addWidget(self.img_label)
        self.center_layout_l.addWidget(self.text_label)
        self.center_layout_l.addWidget(self.seek_slider)
        self.center_layout.addLayout(self.center_layout_l)
        self.center_layout.addWidget(self.time_lcd)
        self.layout.addLayout(self.center_layout)
        self.layout.addStretch(2)
        self.layout.addWidget(self.search_edit)
        self.layout.addWidget(self.search_btn)
        self.layout.addWidget(self.show_current_list)
        self.layout.addWidget(self.help_btn)


class InfoWidget(QWidget):
    def __init__(self, parent=None):
        super(InfoWidget, self).__init__(None)
        self.layout = QVBoxLayout()
        self.music_table_widget = QTableWidget(1, 3)
        self.current_playing_widget = QTableWidget(0, 3)
        self.music_search_widget = QTableWidget(1, 3)

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
            QHeaderView.Stretch)
        self.music_table_widget.setHorizontalHeaderLabels([u'歌曲名',
                                                           u'歌手',
                                                           u'专辑名'])
        self.music_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.music_table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.music_search_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.music_search_widget.setHorizontalHeaderLabels([u'歌曲名',
                                                            u'歌手',
                                                            u'专辑名'])
        self.music_search_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.music_search_widget.horizontalHeader().setResizeMode(
            QHeaderView.Stretch)
        self.music_search_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.current_playing_widget.horizontalHeader().setResizeMode(
            0, QHeaderView.Stretch)
        self.current_playing_widget.setHorizontalHeaderLabels([u'歌曲名',
                                                               u'歌手',
                                                               u'专辑名'])
        self.current_playing_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.current_playing_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

    def set_layouts_prop(self):
        self.layout.addWidget(self.music_search_widget)
        self.layout.addWidget(self.music_table_widget)
        self.layout.addWidget(self.current_playing_widget)


class UiMainWidget(object):
    """
    the main view
    """
    def setup_ui(self, MainWidget):
        self.status = QStatusBar()
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
        self.play_widget.search_edit.setObjectName('search_edit')
        self.play_widget.search_btn.setObjectName('search_btn')

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
        self.play_widget.setFixedHeight(80)
        self.user_widget.setMaximumWidth(220)

    def set_layouts_prop(self):
        self.info_layout.addWidget(self.info_widget)
        self.user_layout.addWidget(self.user_widget)
        self.play_layout.addWidget(self.play_widget)
        self.show_container.addLayout(self.user_layout)
        self.show_container.addLayout(self.info_layout)
        self.control_container.addLayout(self.play_layout)
        self.layout.addLayout(self.control_container)
        self.layout.addLayout(self.show_container)
        self.layout.addWidget(self.status)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
