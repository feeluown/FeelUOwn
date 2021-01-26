import logging
from PyQt5.QtWidgets import (
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
)

from feeluown.utils.utils import use_mpv_old
from feeluown.widgets.separator import Separator

if use_mpv_old():
    from feeluown.widgets.mpv_old import MpvOpenGLWidget
else:
    from feeluown.widgets.mpv import MpvOpenGLWidget

from feeluown.gui.uimain.sidebar import LeftPanel
from feeluown.gui.uimain.page_view import RightPanel
from feeluown.gui.uimain.player_bar import TopPanel

from feeluown.gui.video_show import VideoShowCtl

logger = logging.getLogger(__name__)


class Ui:

    def __init__(self, app):
        self._app = app
        self._layout = QVBoxLayout(app)
        self._top_separator = Separator(parent=app)
        self._splitter = QSplitter(app)

        # NOTE: 以位置命名的部件应该只用来组织界面布局，不要
        # 给其添加任何功能性的函数
        self.top_panel = TopPanel(app, app)
        self.sidebar = self._left_panel_con = LeftPanel(self._app,)
        self.left_panel = self._left_panel_con.p
        self.right_panel = RightPanel(self._app, self._splitter)
        self.bottom_panel = self.right_panel.bottom_panel
        self.mpv_widget = MpvOpenGLWidget(self._app)
        self.frameless_container = None

        # alias
        self.magicbox = self.bottom_panel.magicbox
        self.pc_panel = self.top_panel.pc_panel
        self.table_container = self.right_panel.table_container
        # backward compatible, old name is songs_table_container
        self.songs_table_container = self.table_container
        self.songs_table = self.table_container.songs_table
        self.back_btn = self.bottom_panel.back_btn
        self.forward_btn = self.bottom_panel.forward_btn
        self.toggle_video_btn = self.pc_panel.toggle_video_btn

        self.pc_panel.playlist_btn.clicked.connect(
            lambda: self._app.browser.goto(page='/player_playlist'))

        self._setup_ui()

        # ui controllers
        self.video_show_ctl = VideoShowCtl(self._app, self)

    def _setup_ui(self):
        self._app.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._splitter.setHandleWidth(0)
        self._splitter.addWidget(self._left_panel_con)
        self._splitter.addWidget(self.right_panel)

        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # self._layout.addWidget(self.bottom_panel)
        self._layout.addWidget(self._splitter)
        self._layout.addWidget(self.mpv_widget)
        self._layout.addWidget(self._top_separator)
        self._layout.addWidget(self.top_panel)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.top_panel.layout().setSpacing(0)
        self.top_panel.layout().setContentsMargins(0, 0, 0, 0)

        self._app.resize(880, 600)
