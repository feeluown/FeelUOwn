from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabBar


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
        self.setDrawBase(False)
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
