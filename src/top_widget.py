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


class TopWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_music_btn = QPushButton()
        self.next_music_btn = QPushButton()
        self.play_pause_btn = QPushButton()
        self.text_label = QLabel()
        self.add_to_favorite = QPushButton()
        self.img_label = QLabel()
        self.time_lcd = QLabel()
        # self.seek_slider = Phonon.SeekSlider(self)
        self.search_edit = QLineEdit()
        self.search_btn = QPushButton()
        self.show_current_list = QPushButton()
        self.login_btn = QPushButton()
        self.help_btn = QPushButton()
        self.edit_layout = QHBoxLayout()
        self.center_layout = QHBoxLayout()
        self.center_layout_l = QVBoxLayout()
        self.center_layout_l_top = QHBoxLayout()
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
        self.login_btn.setIcon(QIcon(ICON_PATH + 'login_hover.png'))
        self.play_pause_btn.setIcon(QIcon(ICON_PATH + 'pause_hover.png'))
        self.last_music_btn.setIcon(QIcon(ICON_PATH + 'last_hover.png'))
        self.next_music_btn.setIcon(QIcon(ICON_PATH + 'next_hover.png'))
        self.show_current_list.setIcon(QIcon(ICON_PATH + 'current_play.png'))
        self.help_btn.setIcon(QIcon(ICON_PATH + 'help.png'))

        self.login_btn.setFixedSize(40, 40)

        self.play_pause_btn.setObjectName('play_pause')
        self.last_music_btn.setObjectName('last')
        self.next_music_btn.setObjectName('next')
        self.login_btn.setObjectName('login_btn')

        self.text_label.setText(u'未播放任何歌曲')
        self.text_label.setObjectName(u'music_title')
        self.text_label.setAlignment(Qt.AlignLeft)
        self.img_label.setFixedSize(40, 40)
        self.img_label.setAlignment(Qt.AlignCenter)
        # self.seek_slider.setFixedWidth(500)
        self.time_lcd.setText('00:00')
        # self.search_btn.setText(u'搜索')
        self.search_edit.setFixedHeight(25)
        self.search_btn.setFixedSize(25, 25)
        self.search_edit.setPlaceholderText(u'搜索单曲')
        
        self.add_to_favorite.setObjectName(u'add_to_favorite')
        self.add_to_favorite.setCheckable(True)

    def set_layouts_prop(self):
        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.last_music_btn)
        self.layout.addWidget(self.play_pause_btn)
        self.layout.addWidget(self.next_music_btn)
        self.layout.addStretch(1)
        self.center_layout.addWidget(self.img_label)
        self.center_layout_l.addStretch(1)
        self.center_layout_l_top.addWidget(self.time_lcd)
        self.center_layout_l_top.addStretch(1)
        self.center_layout_l_top.addWidget(self.text_label, 1)
        self.center_layout_l_top.addStretch(1)
        self.center_layout_l_top.addWidget(self.add_to_favorite)
        self.center_layout_l.addStretch(1)
        self.center_layout_l.addLayout(self.center_layout_l_top)
        # self.center_layout_l.addWidget(self.seek_slider)
        self.center_layout_l.addStretch(1)
        self.center_layout.addLayout(self.center_layout_l)
        self.layout.addLayout(self.center_layout)
        self.layout.addStretch(2)
        self.layout.addWidget(self.search_edit)
        self.layout.addWidget(self.search_btn)
        self.layout.addWidget(self.show_current_list)
        self.layout.addWidget(self.help_btn)