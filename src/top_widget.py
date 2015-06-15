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
        self.search_edit = QLineEdit()
        self.login_btn = QPushButton()
        self.help_btn = QPushButton()
        self.slider_play = QSlider()
        self.progress_info = QProgressBar()
        self.edit_layout = QHBoxLayout()
        self.center_layout = QHBoxLayout()
        self.center_layout_l = QVBoxLayout()
        self.center_layout_l_top = QHBoxLayout()
        self.top_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.layout = QVBoxLayout()

        self.set_me()
        self.set_widgets_prop()
        self.set_layouts_prop()

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_me(self):
        # it will conflict with stylesheet, stylesheet has the priority
        # by default, autofill background with Qpalette.Window color(system color)
        # self.setAutoFillBackground(True)
        self.setLayout(self.layout)
        self.set_widgets_effects()

    def set_widgets_effects(self):
        self.dropShadowEffect = QGraphicsDropShadowEffect(self)
        self.dropShadowEffect.setColor(QColor('#222'))
        self.dropShadowEffect.setBlurRadius(3)
        self.dropShadowEffect.setOffset(0, 2)
        self.progress_info.setGraphicsEffect(self.dropShadowEffect)

    def set_widgets_prop(self):

        self.login_btn.setToolTip(u'登录')

        self.login_btn.setFixedSize(25, 25)
        self.help_btn.setFixedSize(25, 25)

        self.text_label.setText(u'未播放任何歌曲')
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.img_label.setFixedSize(55, 55)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.time_lcd.setText('00:00')
        self.search_edit.setFixedHeight(25)
        self.search_edit.setPlaceholderText(u'搜索单曲')
        self.search_edit.setAttribute(Qt.WA_MacShowFocusRect, False)

        self.slider_play.setFixedHeight(15)
        self.slider_play.setOrientation(Qt.Horizontal)
        self.slider_play.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.search_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.progress_info.setFixedHeight(5)
        self.progress_info.setTextVisible(False)
        
        self.add_to_favorite.setCheckable(True)
        self.play_pause_btn.setCheckable(True)
        self.play_pause_btn.setChecked(True)

        self.set_object_name()

    def set_object_name(self):
        self.play_pause_btn.setObjectName('play_pause')
        self.last_music_btn.setObjectName('last')
        self.next_music_btn.setObjectName('next')
        self.login_btn.setObjectName('login_btn')
        self.help_btn.setObjectName('help_btn')
        self.text_label.setObjectName('music_title')
        self.time_lcd.setObjectName('time_label')
        self.add_to_favorite.setObjectName('add_to_favorite')
        self.slider_play.setObjectName('slider_play')
        self.progress_info.setObjectName('progress_info')
        self.img_label.setObjectName('album_label')

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.center_layout.addSpacing(10)
        self.center_layout.addWidget(self.img_label)
        self.center_layout.addSpacing(0)

        self.center_layout_l_top.addSpacing(10)
        self.center_layout_l_top.addWidget(self.time_lcd)
        self.center_layout_l_top.addStretch(1)
        self.center_layout_l_top.addWidget(self.text_label, 1)
        self.center_layout_l_top.addStretch(1)
        self.center_layout_l_top.addWidget(self.add_to_favorite)
        self.center_layout_l_top.addSpacing(10)

        self.center_layout_l.addWidget(self.slider_play)
        self.center_layout_l.addStretch(1)
        self.center_layout_l.addLayout(self.center_layout_l_top)
        self.center_layout_l.addStretch(1)

        self.center_layout.addLayout(self.center_layout_l)

        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.last_music_btn)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.play_pause_btn)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.next_music_btn)
        self.top_layout.addSpacing(30)  # make table widget
        self.top_layout.addLayout(self.center_layout)
        self.top_layout.addSpacing(30)  # make table widget
        self.top_layout.addWidget(self.search_edit)
        self.top_layout.addSpacing(20)
        self.top_layout.addWidget(self.help_btn)
        self.top_layout.addSpacing(5)
        self.top_layout.addWidget(self.login_btn)
        self.top_layout.addSpacing(10)

        self.bottom_layout.addWidget(self.progress_info)

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.bottom_layout)
        self.layout.addSpacing(3)



