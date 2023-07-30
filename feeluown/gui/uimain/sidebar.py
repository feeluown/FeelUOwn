import sys
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy, QScrollArea, \
    QHBoxLayout, QFormLayout, QDialog, QLineEdit, QDialogButtonBox, QMessageBox

from feeluown.collection import CollectionAlreadyExists, CollectionType
from feeluown.gui.widgets import (
    DiscoveryButton, HomeButton, PlusButton, TriagleButton,
)
from feeluown.gui.widgets.playlists import PlaylistsView
from feeluown.gui.components import CollectionListView
from feeluown.gui.widgets.my_music import MyMusicView

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class ListViewContainer(QFrame):

    def __init__(self, label, view, parent=None):
        super().__init__(parent)

        self._btn_length = 14
        self._label = label
        self._view = view
        self._toggle_btn = TriagleButton(length=self._btn_length)
        self.create_btn = PlusButton(length=self._btn_length)
        # Show this button when needed.
        self.create_btn.hide()

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
        self._t_h_layout.addWidget(self.create_btn)
        self._t_h_layout.addSpacing(self._btn_length // 2)
        self._t_h_layout.addWidget(self._toggle_btn)
        self._b_h_layout.addWidget(self._view)

        self._layout.addLayout(self._t_h_layout)
        self._layout.addLayout(self._b_h_layout)
        # XXX: 本意是让 ListViewContainer 下方不要出现多余的空间
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def toggle_view(self):
        if self._view.isVisible():
            self._toggle_btn.set_direction('down')
            self._view.hide()
        else:
            self._toggle_btn.set_direction('up')
            self._view.show()


class LeftPanel(QScrollArea):
    def __init__(self, app: 'GuiApp', parent=None):
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

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent)
        self._app = app

        self.home_btn = HomeButton(height=30, parent=self)
        self.discovery_btn = DiscoveryButton(height=30, padding=0.2, parent=self)
        self.collections_header = QLabel('本地收藏集', self)
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
        self.collections_view = CollectionListView(self._app)

        self.collections_con = ListViewContainer(
            self.collections_header, self.collections_view)
        self.playlists_con = ListViewContainer(
            self.playlists_header, self.playlists_view)
        self.my_music_con = ListViewContainer(
            self.my_music_header, self.my_music_view)

        self.playlists_view.setModel(self._app.pl_uimgr.model)
        self.my_music_view.setModel(self._app.mymusic_uimgr.model)

        self._layout = QVBoxLayout(self)
        self._sub_layout = QVBoxLayout()
        self._top_layout = QVBoxLayout()

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._top_layout)
        self._layout.addLayout(self._sub_layout)

        self._top_layout.setContentsMargins(15, 16, 16, 0)
        self._top_layout.addWidget(self.home_btn)
        self._top_layout.addWidget(self.discovery_btn)
        self._sub_layout.setContentsMargins(16, 8, 16, 0)
        self._sub_layout.addWidget(self.collections_con)
        self._sub_layout.addWidget(self.my_music_con)
        self._sub_layout.addWidget(self.playlists_con)
        self._layout.addStretch(0)

        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.my_music_view.setFrameShape(QFrame.NoFrame)
        self.collections_view.setFrameShape(QFrame.NoFrame)
        self.setFrameShape(QFrame.NoFrame)
        self.collections_con.create_btn.show()
        # 让各个音乐库来决定是否显示这些组件
        self.playlists_con.hide()
        self.my_music_con.hide()

        self.home_btn.clicked.connect(self.show_library)
        self.discovery_btn.clicked.connect(self.show_pool)
        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl))
        self.collections_view.show_collection.connect(
            lambda coll: self._app.browser.goto(page=f'/colls/{coll.identifier}'))
        self.collections_view.remove_collection.connect(self.remove_coll)
        self.collections_con.create_btn.clicked.connect(
            self.popup_collection_adding_dialog)

    def popup_collection_adding_dialog(self):
        dialog = QDialog(self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        layout = QFormLayout(dialog)
        id_edit = QLineEdit(dialog)
        title_edit = QLineEdit(dialog)
        layout.addRow('ID', id_edit)
        layout.addRow('标题', title_edit)
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        layout.addRow('', button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        def create_collection_and_reload():
            fname = id_edit.text()
            title = title_edit.text()
            try:
                self._app.coll_mgr.create(fname, title)
            except CollectionAlreadyExists:
                QMessageBox.warning(self, '警告', f"收藏集 '{fname}' 已存在")
            else:
                self._app.coll_mgr.refresh()

        dialog.accepted.connect(create_collection_and_reload)
        dialog.open()

    def show_library(self):
        coll_library = self._app.coll_mgr.get_coll_library()
        self._app.browser.goto(page=f'/colls/{coll_library.identifier}')

    def show_pool(self):
        coll = self._app.coll_mgr.get(CollectionType.sys_pool)
        self._app.browser.goto(page=f'/colls/{coll.identifier}')

    def remove_coll(self, coll):
        def do():
            self._app.coll_mgr.remove(coll)
            self._app.coll_mgr.refresh()

        box = QMessageBox(QMessageBox.Warning, '提示', f"确认删除收藏集 '{coll.name}' 吗？",
                          QMessageBox.Yes | QMessageBox.No, self)
        box.accepted.connect(do)
        box.open()
