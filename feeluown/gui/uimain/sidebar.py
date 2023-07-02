import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy, QScrollArea, \
    QHBoxLayout

from feeluown.gui.widgets import RecentlyPlayedButton, HomeButton
from feeluown.gui.widgets.playlists import PlaylistsView
from feeluown.gui.widgets.collections import CollectionsView
from feeluown.gui.widgets.my_music import MyMusicView
from feeluown.gui.widgets.textbtn import TextButton


class ListViewContainer(QFrame):
    btn_text_hide = '△'
    btn_text_show = '▼'

    def __init__(self, label, view, parent=None):
        super().__init__(parent)

        self._label = label
        self._view = view
        self._toggle_btn = TextButton(self.btn_text_hide, self)

        self._toggle_btn.clicked.connect(self.toggle_view)
        self.setup_ui()

    def setup_ui(self):
        self._label.setFixedHeight(25)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._t_h_layout = QHBoxLayout()
        self._b_h_layout = QHBoxLayout()
        self._t_h_layout.addWidget(self._label)
        self._t_h_layout.addStretch(0)
        self._t_h_layout.addWidget(self._toggle_btn)
        self._b_h_layout.addWidget(self._view)

        self._layout.addLayout(self._t_h_layout)
        self._layout.addLayout(self._b_h_layout)
        # XXX: 本意是让 ListViewContainer 下方不要出现多余的空间
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def toggle_view(self):
        if self._view.isVisible():
            self.hide_view()
        else:
            self.show_view()

    def show_view(self):
        self._toggle_btn.setText(self.btn_text_hide)
        self._view.show()

    def hide_view(self):
        self._toggle_btn.setText(self.btn_text_show)
        self._view.hide()


class LeftPanel(QScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self.p = _LeftPanel(app, self)
        self.setWidget(self.p)

        if sys.platform.lower() != 'darwin':
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # HELP(cosven): size policy is not working
        # self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.setMaximumWidth(280)

    def sizeHint(self):
        size = super().sizeHint()
        width = min(self._app.width() * 22 // 100, 240)
        return QSize(width, size.height())


class _LeftPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.home_btn = HomeButton(height=30, parent=self)
        self.recently_played_btn = RecentlyPlayedButton(height=30, parent=self)
        self.collections_header = QLabel('本地收藏', self)
        self.collections_header.setToolTip(
            '我们可以在本地建立『收藏集』来收藏自己喜欢的音乐资源\n\n'
            '每个收藏集都以一个独立 .fuo 文件的存在，'
            '将鼠标悬浮在收藏集上，可以查看文件所在路径。\n'
            '新建 fuo 文件，则可以新建收藏集，文件名即是收藏集的名字。\n\n'
            '手动编辑 fuo 文件即可编辑收藏集中的音乐资源，也可以在界面上拖拽来增删歌曲。'
        )
        self.playlists_header = QLabel('歌单列表', self)
        self.my_music_header = QLabel('我的音乐', self)

        self.playlists_view = PlaylistsView(self)
        self.my_music_view = MyMusicView(self)
        self.collections_view = CollectionsView(self)

        self.collections_con = ListViewContainer(
            self.collections_header, self.collections_view)
        self.playlists_con = ListViewContainer(
            self.playlists_header, self.playlists_view)
        self.my_music_con = ListViewContainer(
            self.my_music_header, self.my_music_view)

        self.playlists_view.setModel(self._app.pl_uimgr.model)
        self.my_music_view.setModel(self._app.mymusic_uimgr.model)
        self.collections_view.setModel(self._app.coll_uimgr.model)

        self._layout = QVBoxLayout(self)
        self._sub_layout = QVBoxLayout()
        self._top_layout = QVBoxLayout()

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._top_layout)
        self._layout.addLayout(self._sub_layout)

        self._top_layout.addWidget(self.home_btn)
        self._top_layout.addWidget(self.recently_played_btn)
        self._top_layout.setContentsMargins(15, 16, 16, 0)
        self._sub_layout.setContentsMargins(16, 8, 16, 0)
        self._sub_layout.addWidget(self.collections_con)
        self._sub_layout.addWidget(self.my_music_con)
        self._sub_layout.addWidget(self.playlists_con)
        self._layout.addStretch(0)

        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.my_music_view.setFrameShape(QFrame.NoFrame)
        self.collections_view.setFrameShape(QFrame.NoFrame)
        self.setFrameShape(QFrame.NoFrame)
        # 让各个音乐库来决定是否显示这些组件
        self.playlists_con.hide()
        self.my_music_con.hide()

        self.home_btn.clicked.connect(self.show_library)
        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl))
        self.collections_view.show_collection.connect(self.show_coll)

    def show_library(self):
        coll_library = self._app.coll_uimgr.get_coll_library()
        coll_id = self._app.coll_uimgr.get_coll_id(coll_library)
        self._app.browser.goto(page=f'/colls/{coll_id}')

    def show_coll(self, coll):
        coll_id = self._app.coll_uimgr.get_coll_id(coll)
        self._app.browser.goto(page='/colls/{}'.format(coll_id))
