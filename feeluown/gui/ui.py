import logging
from PyQt5.QtWidgets import QSizePolicy, QSplitter, QVBoxLayout

from feeluown.gui.widgets.separator import Separator
from feeluown.gui.widgets.settings import SettingsDialog
from feeluown.gui.widgets.messageline import MessageLine
from feeluown.gui.widgets.mpv_ import MpvOpenGLWidget

from feeluown.gui.uimain.lyric import LyricWindow
from feeluown.gui.uimain.sidebar import LeftPanel
from feeluown.gui.uimain.page_view import RightPanel
from feeluown.gui.uimain.player_bar import TopPanel
from feeluown.gui.uimain.playlist_overlay import PlaylistOverlay
from feeluown.gui.uimain.nowplaying_overlay import NowplayingOverlay

logger = logging.getLogger(__name__)


class Ui:

    def __init__(self, app):
        self._app = app
        # Let the following widgets access ui object during init.
        self._app.ui = self
        self._layout = QVBoxLayout(app)
        self._top_separator = Separator(app)
        self._splitter = QSplitter(app)

        # Create widgets that don't rely on other widgets first.
        try:
            from feeluown.gui.uimain.ai_chat import create_aichat_overlay
        except ImportError as e:
            logger.warning(f'AIChatOverlay is not available: {e}')
            self.ai_chat_overlay = None
        else:
            self.ai_chat_overlay = create_aichat_overlay(app, parent=app)
            self.ai_chat_overlay.hide()
        self.lyric_window = LyricWindow(self._app)
        self.lyric_window.hide()
        self.playlist_overlay = PlaylistOverlay(app, parent=app)
        self.nowplaying_overlay = NowplayingOverlay(app, parent=app)

        # NOTE: 以位置命名的部件应该只用来组织界面布局，不要
        # 给其添加任何功能性的函数
        self._message_line = MessageLine()
        self.top_panel = TopPanel(app, app)
        self.sidebar = self._left_panel_con = LeftPanel(self._app)
        self.left_panel = self._left_panel_con.p
        self.page_view = self.right_panel = RightPanel(self._app, self._splitter)
        self.toolbar = self.bottom_panel = self.right_panel.bottom_panel
        self.mpv_widget = MpvOpenGLWidget(self._app)

        # alias
        self.magicbox = self.bottom_panel.magicbox
        self.player_bar = self.pc_panel = self.top_panel.pc_panel
        self.table_container = self.right_panel.table_container
        # backward compatible, old name is songs_table_container
        self.songs_table_container = self.table_container
        self.songs_table = self.table_container.songs_table
        self.back_btn = self.bottom_panel.back_btn
        self.forward_btn = self.bottom_panel.forward_btn

        self.toolbar.settings_btn.clicked.connect(self._open_settings_dialog)

        self._setup_ui()

    def _setup_ui(self):
        self._app.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._splitter.setHandleWidth(0)
        self._splitter.addWidget(self._left_panel_con)
        self._splitter.addWidget(self.right_panel)
        self._message_line.hide()
        self.playlist_overlay.hide()
        self.nowplaying_overlay.hide()

        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._layout.addWidget(self._splitter)
        self._layout.addWidget(self.mpv_widget)
        self._layout.addWidget(self._message_line)
        self._layout.addWidget(self._top_separator)
        self._layout.addWidget(self.top_panel)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.top_panel.layout().setSpacing(0)
        self.top_panel.layout().setContentsMargins(0, 0, 0, 0)

        self._app.resize(960, 600)

    def _open_settings_dialog(self):
        dialog = SettingsDialog(self._app, self._app)
        dialog.exec()

    def toggle_player_bar(self):
        if self.top_panel.isVisible():
            self.top_panel.hide()
            self._top_separator.hide()
        else:
            self.top_panel.show()
            self._top_separator.show()
