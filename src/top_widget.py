# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class MusicInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.album_img_label = QLabel()
        self.music_countdown_label = QLabel()
        self.music_slider = QSlider()
        self.music_name_label = QLabel()
        self.love_music_btn = QPushButton()
        self.play_mv_btn = QPushButton("MV")
        self.show_lyric_btn = QPushButton("词")

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self._customize_object_name()
        self._customize_widgets_props()
        self._customize_layout()

    def _customize_widgets_props(self):
        self.music_name_label.setText("未播放任何歌曲")
        self.music_name_label.setAlignment(Qt.AlignCenter)
        self.music_name_label.setMaximumWidth(300)
        self.music_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.album_img_label.setFixedSize(55, 55)
        self.album_img_label.setAlignment(Qt.AlignCenter)
        self.music_countdown_label.setText('00:00')

        self.love_music_btn.setChecked(True)

        self.music_slider.setFixedHeight(15)
        self.music_slider.setOrientation(Qt.Horizontal)
        self.music_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _customize_object_name(self):
        self.album_img_label.setObjectName("album_img_label")
        self.music_countdown_label.setObjectName("music_countdown_label")
        self.music_slider.setObjectName("music_slider")
        self.music_name_label.setObjectName("music_name_label")
        self.love_music_btn.setObjectName("love_music_btn")
        self.play_mv_btn.setObjectName("play_mv_btn")
        self.show_lyric_btn.setObjectName("show_lyric_btn")
        self.setObjectName("music_info_widget")

    def _customize_layout(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        music_function_container = QWidget(self)
        music_function_container_layout = QVBoxLayout(music_function_container)
        music_function_container_layout.setContentsMargins(0, 0, 0, 0)
        music_function_container_layout.setSpacing(0)
        music_function_container.setLayout(music_function_container_layout)
        music_function_container_layout.addWidget(self.music_slider)

        music_function_container_sub = QWidget(music_function_container)
        music_function_container_sub_layout = QHBoxLayout(music_function_container_sub)
        music_function_container_sub_layout.setContentsMargins(0, 0, 0, 0)
        music_function_container_sub_layout.setSpacing(0)
        music_function_container_sub.setLayout(music_function_container_sub_layout)

        music_function_container_layout.addWidget(music_function_container_sub)

        music_function_container_sub_layout.addSpacing(10)
        music_function_container_sub_layout.addWidget(self.music_countdown_label)
        music_function_container_sub_layout.addStretch(1)
        music_function_container_sub_layout.addWidget(self.music_name_label)
        music_function_container_sub_layout.addStretch(1)

        music_btns_layout = QHBoxLayout(music_function_container_sub)
        music_function_container_sub_layout.addLayout(music_btns_layout)

        music_btns_layout.addWidget(self.play_mv_btn)
        music_btns_layout.addSpacing(10)
        music_btns_layout.addWidget(self.show_lyric_btn)
        music_btns_layout.addSpacing(10)
        music_btns_layout.addWidget(self.love_music_btn)

        self.layout.addWidget(self.album_img_label)
        self.layout.addWidget(music_function_container)


class TopWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_music_btn = QPushButton()
        self.next_music_btn = QPushButton()
        self.play_pause_btn = QPushButton()
        self.search_edit = QLineEdit()
        self.login_btn = QPushButton("~")
        self.login_label = QLabel()
        self.show_current_list = QPushButton()
        self.edit_layout = QHBoxLayout()

        self.music_info_container = MusicInfoWidget()

        self.top_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.layout = QVBoxLayout()

        self.setLayout(self.layout)
        self.set_widgets_prop()
        self.set_layouts_prop()
        self.init_widget()

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.y
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def init_widget(self):
        self.login_label.close()
        self.music_info_container.love_music_btn.close()
        self.music_info_container.play_mv_btn.close()

    def set_widgets_prop(self):
        self.login_btn.setToolTip(u'登录')

        self.login_label.setFixedSize(30, 30)
        self.login_btn.setFixedSize(30, 30)
        self.show_current_list.setFixedSize(30, 30)
        self.show_current_list.setToolTip(u'显示当前播放列表')

        self.search_edit.setFixedHeight(30)
        self.search_edit.setPlaceholderText(u'搜索歌曲')
        self.search_edit.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.search_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.play_pause_btn.setCheckable(True)
        self.play_pause_btn.setChecked(True)

        self.music_info_container.setFixedHeight(57)
        self.setFixedHeight(57)

        self.set_object_name()

    def set_object_name(self):
        self.play_pause_btn.setObjectName('play_pause')
        self.last_music_btn.setObjectName('last')
        self.next_music_btn.setObjectName('next')
        self.login_btn.setObjectName('login_btn')
        self.login_label.setObjectName('login_label')
        self.show_current_list.setObjectName('show_current_list')

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.last_music_btn)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.play_pause_btn)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.next_music_btn)
        self.top_layout.addSpacing(30)  # make table widget
        self.top_layout.addWidget(self.music_info_container)
        self.top_layout.addSpacing(20)  # make table widget
        self.top_layout.addWidget(self.search_edit)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.show_current_list)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.login_btn)
        self.top_layout.addSpacing(10)
        self.top_layout.addWidget(self.login_label)
        self.top_layout.addSpacing(5)

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.bottom_layout)
        self.layout.addSpacing(3)