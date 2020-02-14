import logging
from PyQt5.QtWidgets import (
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
)

from feeluown.widgets.separator import Separator
from feeluown.widgets.mpv import MpvOpenGLWidget
from feeluown.containers.left_panel import LeftPanel
from feeluown.containers.right_panel import RightPanel
from feeluown.containers.top_panel import TopPanel

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
        self._left_panel_con = LeftPanel(self._app,)
        self.left_panel = self._left_panel_con.p
        self.right_panel = RightPanel(self._app, self._splitter)
        self.bottom_panel = self.right_panel.bottom_panel
        self.mpv_widget = MpvOpenGLWidget(self._app)

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

        self.pc_panel.playlist_btn.clicked.connect(self.show_player_playlist)
        self.pc_panel.mv_btn.clicked.connect(self._play_mv)
        self.toggle_video_btn.clicked.connect(self._toggle_video)
        self._app.player.video_format_changed.connect(
            self.on_video_format_changed, aioqueue=True)

        self.show_video_widget()
        self._app.initialized.connect(lambda app: self.hide_video_widget(), weak=False)
        self._setup_ui()

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

    def _play_mv(self):
        song = self._app.player.current_song
        mv = song.mv if song else None
        if mv is not None:
            if mv.meta.support_multi_quality:
                media, _ = mv.select_media()
            else:
                media = mv.media
            self.toggle_video_btn.show()
            self.show_video_widget()
            self._app.player.play(media)

    def show_player_playlist(self):
        self.table_container.show_player_playlist()

    def on_video_format_changed(self, vformat):
        """when video is available, show toggle_video_btn"""
        if vformat is None:
            self.hide_video_widget()
            self.toggle_video_btn.hide()
        else:
            self.toggle_video_btn.show()

    def _toggle_video(self):
        if self.mpv_widget.isVisible():
            self.hide_video_widget()
        else:
            self.show_video_widget()

    def hide_video_widget(self):
        self.mpv_widget.hide()
        self._splitter.show()
        self.bottom_panel.show()
        self.pc_panel.toggle_video_btn.setText('△')

    def show_video_widget(self):
        self.bottom_panel.hide()
        self._splitter.hide()
        self.mpv_widget.show()
        self.pc_panel.toggle_video_btn.setText('▽')
