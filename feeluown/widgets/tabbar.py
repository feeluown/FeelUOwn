from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabBar, QWidget, QRadioButton, QHBoxLayout


class TableTabBarV2(QWidget):
    """
    We tried to use QTabBar as the base class, we found that QTabBar's UI
    is hard to customize.
    """

    show_songs_needed = pyqtSignal()
    show_artists_needed = pyqtSignal()
    show_albums_needed = pyqtSignal()
    show_desc_needed = pyqtSignal()
    show_contributed_albums_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.songs_btn = QRadioButton('歌曲', self)
        self.albums_btn = QRadioButton('专辑', self)
        self.desc_btn = QRadioButton('简介', self)
        self.contributed_btn = QRadioButton('参与作品', self)
        self._layout = QHBoxLayout(self)

        self.songs_btn.clicked.connect(self.show_songs_needed.emit)
        self.albums_btn.clicked.connect(self.show_albums_needed.emit)
        self.desc_btn.clicked.connect(self.show_desc_needed.emit)
        self.contributed_btn.clicked.connect(self.show_contributed_albums_needed.emit)

        # TODO: let caller to decide which btn is checked by default
        self.songs_btn.setChecked(True)
        self._setup_ui()

    def artist_mode(self):
        pass

    def _setup_ui(self):
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.desc_btn)
        self._layout.addWidget(self.songs_btn)
        self._layout.addWidget(self.albums_btn)
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
