# -*- coding=utf8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QHBoxLayout, QStyleOption, QStyle, QWidget, \
    QVBoxLayout

from feeluown.widgets.music_table import TracksTableWidget
from feeluown.widgets.tracks_widget import TracksWidget


class MusicWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)

        self.tracks_table_widget = TracksTableWidget()
        self.tracks_widget = TracksWidget()
        self.layout.addWidget(self.tracks_widget)
        self.layout.addWidget(self.tracks_table_widget)

        self._set_layouts_prop()

    def _set_layouts_prop(self):
        self.layout.setContentsMargins(10, 0, 0, 5)
        self.layout.setSpacing(0)

    def load_playlist(self, playlist_model):
        tracks = playlist_model['tracks']
        self.tracks_table_widget.set_songs(tracks)
        self.tracks_widget.load_img(playlist_model['coverImgUrl'])
        self.tracks_widget.set_title(playlist_model['name'])


class RightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.webview = MusicWidget()

        self.set_me()
        self.set_widgets_prop()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

    def paintEvent(self, event):
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

    def set_widgets_prop(self):
        self.webview.setObjectName("webview")

    def set_layouts_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.webview)
