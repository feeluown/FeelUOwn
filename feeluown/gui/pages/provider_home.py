import logging
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame

from feeluown.gui.widgets.my_music import MyMusicView
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.playlists import PlaylistsView


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


logger = logging.getLogger(__name__)


async def render(req, identifier, **kwargs):
    app: 'GuiApp' = req.ctx['app']
    provider = app.library.get(identifier)
    app.ui.right_panel.set_body(View(app, provider))


class View(QWidget):
    def __init__(self, app: 'GuiApp', provider, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._app = app
        self._provider = provider

        self.title = LargeHeader(self._provider.name, parent=self)
        self.my_music_header = MidHeader('我的音乐', parent=self)
        self.my_music_view = MyMusicView(parent=self)
        self.playlists_header = MidHeader('歌单列表', parent=self)
        self.playlists_view = PlaylistsView(parent=self)

        self.my_music_view.setModel(self._app.mymusic_uimgr.model)
        self.playlists_view.setModel(self._app.pl_uimgr.model)

        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl))

        self._playlists_scroll = QScrollArea(self)
        self._playlists_scroll.setWidget(self.playlists_view)
        self._playlists_scroll.setWidgetResizable(True)
        self.playlists_view.setFrameShape(QFrame.NoFrame)

        self._layout = QVBoxLayout(self)
        self._body_layout = QHBoxLayout()
        self._l_layout = QVBoxLayout()
        self._r_layout = QVBoxLayout()

        self._layout.addWidget(self.title)
        self._layout.addLayout(self._body_layout)

        self._body_layout.addLayout(self._l_layout)
        self._body_layout.addLayout(self._r_layout)

        self._l_layout.addWidget(self.my_music_header)
        self._l_layout.addWidget(self.my_music_view)
        self._l_layout.addStretch(0)

        self._r_layout.addWidget(self.playlists_header)
        self._r_layout.addWidget(self._playlists_scroll)
        self._r_layout.addStretch(0)
