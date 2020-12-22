import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy, QScrollArea, \
    QHBoxLayout

from feeluown.gui.helpers import use_mac_theme
from feeluown.widgets.playlists import PlaylistsView
from feeluown.widgets.provider import ProvidersView
from feeluown.widgets.collections import CollectionsView
from feeluown.widgets.my_music import MyMusicView
from feeluown.widgets.textbtn import TextButton


class ListViewContainer(QFrame):
    btn_text_hide = '△'
    btn_text_show = '▼'

    def __init__(self, label, view, parent=None):
        super().__init__(parent)

        self._label = label
        self._view = view
        self._toggle_btn = TextButton(self.btn_text_hide, self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._h_layout = QHBoxLayout()
        label.setFixedHeight(25)
        self._h_layout.addWidget(label)
        self._h_layout.addStretch(0)
        self._h_layout.addWidget(self._toggle_btn)
        self._h_layout.addSpacing(10)
        self._layout.addLayout(self._h_layout)
        self._layout.addWidget(view)
        self._layout.addStretch(0)
        # XXX: 本意是让 ListViewContainer 下方不要出现多余的空间
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self._toggle_btn.clicked.connect(self.toggle_view)

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


class _LeftPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.library_header = QLabel('音乐提供方', self)
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
        self.providers_view = ProvidersView(self)
        self.my_music_view = MyMusicView(self)
        self.collections_view = CollectionsView(self)

        self.providers_con = ListViewContainer(
            self.library_header, self.providers_view)
        self.collections_con = ListViewContainer(
            self.collections_header, self.collections_view)
        self.playlists_con = ListViewContainer(
            self.playlists_header, self.playlists_view)
        self.my_music_con = ListViewContainer(
            self.my_music_header, self.my_music_view)

        self.providers_view.setModel(self._app.pvd_uimgr.model)
        self.playlists_view.setModel(self._app.pl_uimgr.model)
        self.my_music_view.setModel(self._app.mymusic_uimgr.model)
        self.collections_view.setModel(self._app.coll_uimgr.model)

        self._layout = QVBoxLayout(self)

        if use_mac_theme():
            self._layout.setSpacing(0)
            self._layout.setContentsMargins(6, 4, 0, 0)
        self._layout.addWidget(self.providers_con)
        self._layout.addWidget(self.collections_con)
        self._layout.addWidget(self.my_music_con)
        self._layout.addWidget(self.playlists_con)
        self._layout.addStretch(0)

        self.providers_view.setFrameShape(QFrame.NoFrame)
        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.my_music_view.setFrameShape(QFrame.NoFrame)
        self.collections_view.setFrameShape(QFrame.NoFrame)
        self.setFrameShape(QFrame.NoFrame)
        # 让各个音乐库来决定是否显示这些组件
        self.playlists_con.hide()
        self.my_music_con.hide()

        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl))
        self.collections_view.show_collection.connect(self.show_coll)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(230, size.height())

    def show_coll(self, coll):
        coll_id = self._app.coll_uimgr.get_coll_id(coll)
        self._app.browser.goto(page='/colls/{}'.format(coll_id))
