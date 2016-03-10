# -*- coding=utf-8 -*-


"""
ui design

every basic widget (including user,info,play) class has three public \
funcition to set child widget properties.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyleOption, QStyle, QWidget, \
    QVBoxLayout

from feeluown.widgets.music_table import TracksTableWidget,\
    TracksTableOptionsWidget


class MusicWidget(QWidget):
    signal_play_song = pyqtSignal([int])
    signal_play_songs = pyqtSignal([list])
    signal_play_song_ids = pyqtSignal([list])
    signal_play_mv = pyqtSignal([int])
    signal_search_album = pyqtSignal([int])
    signal_search_artist = pyqtSignal([int])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.tracks_table_widget = TracksTableWidget()
        self.tracks_table_options_widget = TracksTableOptionsWidget()
        self.layout.addWidget(self.tracks_table_options_widget)
        self.layout.addWidget(self.tracks_table_widget)

        self._set_layout_props()
        self._bind_signal()

    def _set_layout_props(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def _bind_signal(self):
        self.tracks_table_widget.signal_play_music.connect(
            self.signal_play_song.emit)
        self.tracks_table_options_widget.play_all_btn.clicked.connect(
            self._play_songs)
        self.tracks_table_widget.signal_play_mv.connect(
            self.signal_play_mv.emit)
        self.tracks_table_widget.signal_search_album.connect(
            self.signal_search_album.emit)
        self.tracks_table_widget.signal_search_artist.connect(
            self.signal_search_artist.emit)

    def _play_songs(self):
        songs = self.tracks_table_widget.songs
        if self.tracks_table_widget.is_songs_brief():
            song_ids = [song['id'] for song in songs]
            self.signal_play_song_ids.emit(song_ids)
        else:
            self.signal_play_songs.emit(songs)

    def load_playlist(self, playlist_model):
        tracks = playlist_model['tracks']
        self.tracks_table_widget.set_songs(tracks, 0)

    def load_artist(self, artist_detail_model):
        tracks = artist_detail_model['hotSongs']
        self.tracks_table_widget.set_songs(tracks, 2)

    def load_album(self, album_detail_model):
        tracks = album_detail_model['songs']
        self.tracks_table_widget.set_songs(tracks, 3)

    def load_brief_songs(self, songs):
        self.tracks_table_widget.set_songs(songs, 4)

    def load_songs(self, songs):
        print (songs)


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
