from enum import Enum

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabBar, QWidget, QRadioButton, QHBoxLayout


def mode(func):
    def wrapper(this):
        this.songs_btn.hide()
        this.albums_btn.hide()
        this.artists_btn.hide()
        this.playlists_btn.hide()
        this.desc_btn.hide()
        this.contributed_btn.hide()
        this.videos_btn.hide()
        func(this)
    return wrapper


class Tab(Enum):
    songs = 1
    albums = 2
    artists = 3
    playlists = 4
    videos = 5

    desc = 8

    contributed = 16


class TableTabBarV2(QWidget):
    """
    We tried to use QTabBar as the base class, we found that QTabBar's UI
    is hard to customize.
    """

    show_songs_needed = pyqtSignal()
    show_artists_needed = pyqtSignal()
    show_albums_needed = pyqtSignal()
    show_playlists_needed = pyqtSignal()
    show_videos_needed = pyqtSignal()
    show_desc_needed = pyqtSignal()
    show_contributed_albums_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.songs_btn = QRadioButton('歌曲', self)
        self.albums_btn = QRadioButton('专辑', self)
        self.artists_btn = QRadioButton('歌手', self)
        self.playlists_btn = QRadioButton('歌单', self)
        self.videos_btn = QRadioButton('视频', self)
        self.desc_btn = QRadioButton('简介', self)
        self.contributed_btn = QRadioButton('参与作品', self)
        self._layout = QHBoxLayout(self)

        self.songs_btn.clicked.connect(self.show_songs_needed.emit)
        self.albums_btn.clicked.connect(self.show_albums_needed.emit)
        self.artists_btn.clicked.connect(self.show_artists_needed.emit)
        self.desc_btn.clicked.connect(self.show_desc_needed.emit)
        self.contributed_btn.clicked.connect(self.show_contributed_albums_needed.emit)
        self.playlists_btn.clicked.connect(self.show_playlists_needed.emit)
        self.videos_btn.clicked.connect(self.show_videos_needed.emit)

        self._tab_btn_mapping = {
            Tab.songs: self.songs_btn,
            Tab.albums: self.albums_btn,
            Tab.artists: self.artists_btn,
            Tab.playlists: self.playlists_btn,
            Tab.videos: self.videos_btn,
            Tab.desc: self.desc_btn,
            Tab.contributed: self.contributed_btn,
        }

        self.check_default()
        self._setup_ui()

    def check_default(self):
        self.songs_btn.setChecked(True)

    def check(self, tab):
        self._tab_btn_mapping[tab].setChecked(True)

    @mode
    def artist_mode(self):
        self.songs_btn.show()
        self.albums_btn.show()
        self.desc_btn.show()
        self.contributed_btn.show()

    @mode
    def album_mode(self):
        self.songs_btn.show()
        self.desc_btn.show()

    @mode
    def library_mode(self):
        self.songs_btn.show()
        self.albums_btn.show()
        self.artists_btn.show()
        self.playlists_btn.show()
        self.videos_btn.show()

    def _setup_ui(self):
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.desc_btn)
        self._layout.addWidget(self.songs_btn)
        self._layout.addWidget(self.artists_btn)
        self._layout.addWidget(self.albums_btn)
        self._layout.addWidget(self.playlists_btn)
        self._layout.addWidget(self.videos_btn)
        self._layout.addWidget(self.contributed_btn)


class TableTabBar(QTabBar):
    song = '歌曲'
    artist = '歌手'
    album = '专辑'
    contributed_albums = '参与作品'

    show_songs_needed = pyqtSignal()
    show_artists_needed = pyqtSignal()
    show_albums_needed = pyqtSignal()
    show_contributed_albums_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.tabBarClicked.connect(self.on_index_changed)
        self.setExpanding(False)
        # self.setDrawBase(False)
        self.setShape(QTabBar.TriangularNorth)

    def use(self, *tabs):
        i = self.count() - 1
        while i >= 0:
            self.removeTab(i)
            i = i - 1
        for tab in tabs:
            self.addTab(tab)

    def artist_mode(self):
        self.use(TableTabBar.song,
                 TableTabBar.album,
                 TableTabBar.contributed_albums)

    def library_mode(self):
        self.use(TableTabBar.song,
                 TableTabBar.artist,
                 TableTabBar.album,
                 TableTabBar.contributed_albums)

    def on_index_changed(self, index):
        text = self.tabText(index)
        if text == self.song:
            self.show_songs_needed.emit()
        elif text == self.artist:
            self.show_artists_needed.emit()
        elif text == self.album:
            self.show_albums_needed.emit()
        else:
            self.show_contributed_albums_needed.emit()
