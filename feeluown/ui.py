# -*- coding=utf8 -*-


"""
ui design

every basic widget class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtWidgets import *

from feeluown.left_widget import LeftScrollArea
from feeluown.right_widget import RightWidget
from feeluown.top_widget import TopWidget
from feeluown.widgets.statusbar import StatusBar


class UiMainWidget(object):
    """
    the main view
    """
    def setup_ui(self, MainWidget):
        self.status = StatusBar()
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
        self._alias_name()

    def _alias_name(self):
        self.PLAY_OR_PAUSE = self.top_widget.play_pause_btn
        self.PLAY_PREVIOUS_SONG_BTN = self.top_widget.last_music_btn
        self.PLAY_NEXT_SONG_BTN = self.top_widget.next_music_btn
        self.SEARCH_BOX = self.top_widget.search_edit
        self.LOGIN_BTN = self.top_widget.login_btn
        self.SHOW_CURRENT_SONGS = self.top_widget.show_current_list

        self.SHOW_DESKTOP_MINI = self.status.desktop_mini_btn

        self.ALBUM_IMG_LABEL = self.top_widget.music_info_container.album_img_label
        self.SONG_COUNTDOWN_LABEL = self.top_widget.music_info_container.music_countdown_label
        self.SONG_PROGRESS_SLIDER = self.top_widget.music_info_container.music_slider
        self.SONG_NAME_LABEL = self.top_widget.music_info_container.music_name_label
        self.LOVE_SONG_BTN = self.top_widget.music_info_container.love_music_btn
        self.PLAY_MV_BTN = self.top_widget.music_info_container.play_mv_btn
        self.SIMI_SONGS_BTN = self.top_widget.music_info_container.similar_song_btn
        self.SHOW_LYRIC_BTN = self.top_widget.music_info_container.show_lyric_btn
        self.AVATAR_LABEL = self.top_widget.login_label

        self.NEW_PLAYLIST_BTN = self.left_widget.central_widget.new_playlist_btn
        self.SPREAD_BTN_FOR_MY_LIST = self.left_widget.central_widget.create_fold_spread_btn
        self.SPREAD_BTN_FOR_COLLECTION = self.left_widget.central_widget.collection_fold_spread_btn
        self.SPREAD_BTN_FOR_LOCAL = self.left_widget.central_widget.local_fold_spread_btn

        self.FM_ITEM = self.left_widget.central_widget.fm_item
        self.MY_LIST_WIDGET = self.left_widget.central_widget.create_list_widget
        self.COLLECTION_LIST_WIDGET = self.left_widget.central_widget.collection_list_widget
        self.LOCAL_LIST_WIDGET = self.left_widget.central_widget.local_list_widget

        self.STATUS_BAR = self.status
        self.PROGRESS = self.progress_info
        self.WEBVIEW = self.right_widget.webview

        self.TOP_WIDGET = self.top_widget
        self.LEFT_WIDGET = self.left_widget
        self.RIGHT_WIDGET = self.right_widget

        self.QUIT_ACTION = self.top_widget.login_label.quit_action

    def set_widgets(self):
        self.set_widgets_size()
        self.set_object_name()

        self.progress_info.setFixedHeight(2)
        self.progress_info.setTextVisible(False)
        self.progress_info.setRange(0, 100)

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
