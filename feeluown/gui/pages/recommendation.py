from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from feeluown.utils.reader import create_reader
from feeluown.utils.aio import run_fn
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.img_card_list import (
    PlaylistCardListView, PlaylistCardListModel, PlaylistFilterProxyModel,
    PlaylistCardListDelegate,
)

from feeluown.library import SupportsRecListDailyPlaylists, SupportsRecListDailySongs

from feeluown.gui.widgets import CalendarButton, RankButton
from feeluown.gui.helpers import fetch_cover_wrapper


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


async def render(req, **kwargs):
    app: 'GuiApp' = req.ctx['app']

    view = View(app)
    app.ui.right_panel.set_body(view)
    await view.render()


class View(QWidget):
    def __init__(self, app: 'GuiApp'):
        super().__init__(parent=None)
        self._app = app

        self.header_title = LargeHeader()
        self.header_playlist_list = MidHeader()
        self.playlist_list_view = PlaylistCardListView(fixed_row_count=1)
        self.playlist_list_view.setItemDelegate(
            PlaylistCardListDelegate(self.playlist_list_view,
                                     card_min_width=100,))
        self.daily_songs_btn = CalendarButton('每日推荐', parent=self)
        self.rank_btn = RankButton(parent=self)
        self.daily_songs_btn.setMinimumWidth(150)
        self.rank_btn.setMinimumWidth(150)

        self.header_title.setText('发现音乐')
        self.header_playlist_list.setText('个性化推荐')
        self.rank_btn.setDisabled(True)
        self.rank_btn.setToolTip('未实现，欢迎 PR！')

        self._layout = QVBoxLayout(self)
        self._setup_ui()

        self.playlist_list_view.show_playlist_needed.connect(
            lambda model: self._app.browser.goto(model=model))
        self.daily_songs_btn.clicked.connect(
            lambda: self._app.browser.goto(page='/rec/daily_songs'))
        self.rank_btn.clicked.connect(
            lambda: self._app.show_msg('未实现，欢迎 PR！'))

    def _setup_ui(self):
        self._h_layout = QHBoxLayout()
        self._h_layout.addWidget(self.daily_songs_btn)
        self._h_layout.addSpacing(10)
        self._h_layout.addWidget(self.rank_btn)
        self._h_layout.addStretch(0)

        self._layout.setContentsMargins(20, 10, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.header_title)
        self._layout.addSpacing(10)
        self._layout.addLayout(self._h_layout)
        self._layout.addSpacing(30)
        self._layout.addWidget(self.header_playlist_list)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.playlist_list_view)
        self._layout.addStretch(0)

    async def render(self):
        pvd_ui = self._app.current_pvd_ui_mgr.get()
        if pvd_ui is None:
            self._app.show_msg('wtf!')
            return

        provider = pvd_ui.provider
        if isinstance(provider, SupportsRecListDailyPlaylists):
            playlists = await run_fn(provider.rec_list_daily_playlists)
            model = PlaylistCardListModel(
                create_reader(playlists),
                fetch_cover_wrapper(self._app),
                {p.identifier: p.name for p in self._app.library.list()})
            filter_model = PlaylistFilterProxyModel()
            filter_model.setSourceModel(model)
            self.playlist_list_view.setModel(filter_model)

        if not isinstance(provider, SupportsRecListDailySongs):
            self.daily_songs_btn.setDisabled(True)
