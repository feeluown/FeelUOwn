from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import QEvent, QSize
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QTabBar,
    QStackedWidget,
    QSplitter,
)

from feeluown.gui.components import PlayerProgressSliderAndLabel
from feeluown.gui.components.btns import MediaButtonsV2
from feeluown.gui.components.nowplaying import (
    NowplayingArtwork,
    NowplayingLyricView,
    NowplayingCommentListView,
    NowplayingPlayerPlaylistView,
    NowplayingSimilarSongsView,
)
from feeluown.gui.components.line_song import TwoLineSongLabel
from feeluown.gui.helpers import set_default_font_families, esc_hide_widget

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class CtlButtons(QWidget):

    def __init__(self, app: 'GuiApp', parent: 'PlayerPanel'):
        super().__init__(parent=parent)
        self._app = app

        self.media_btns = MediaButtonsV2(app, button_width=36, parent=self)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.media_btns)


class PlayerPanel(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.artwork_view = NowplayingArtwork(app, self)
        self.title_label = TwoLineSongLabel(app, self)
        self.ctl_btns = CtlButtons(app, parent=self)
        self.progress = PlayerProgressSliderAndLabel(app, parent=self)

        self._layout = QVBoxLayout(self)
        self.setup_ui()

        self.artwork_view.mv_btn.clicked.connect(self.play_mv)
        self.ctl_btns.media_btns.toggle_video_btn.clicked.connect(
            self.keep_and_enter_video_mode
        )
        self._app.player.media_loaded_v2.connect(
            self.on_media_loaded, aioqueue=True
        )
        self._keep_video_mode = False

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 11, 0)
        self._layout.setSpacing(0)
        # Put the cover_label in a vboxlayout and add strech around it,
        # so that cover_label's sizehint is respected.
        self._layout.addWidget(self.title_label)
        self._layout.addSpacing(20)
        self._layout.addWidget(self.artwork_view)
        self._layout.setStretch(self._layout.indexOf(self.artwork_view), 1)
        self._layout.addSpacing(20)
        self._layout.addStretch(0)
        self._layout.addWidget(self.progress)
        self._layout.addWidget(self.ctl_btns)

    def play_mv(self):
        self._app.playlist.set_current_model(self._app.playlist.current_song_mv)
        self.enter_video_mode()

    def keep_and_enter_video_mode(self):
        self._keep_video_mode = True
        self.enter_video_mode()

    def unkeep_and_enter_cover_mode(self):
        self._keep_video_mode = False
        self.enter_cover_mode()

    def enter_video_mode(self):
        # FIXME: should call watch_mgr.set_mode
        self._app.watch_mgr.exit_pip_mode()
        self._app.watch_mgr.exit_fullwindow_mode()
        video_widget = self._app.ui.mpv_widget
        video_widget.overlay_auto_visible = True
        if video_widget.parent() == self.artwork_view:
            video_widget.show()
            self.artwork_view.set_body(video_widget)
        else:
            with video_widget.change_parent():
                # Remember always give video_widget a parent first and
                # then show it. Otherwise, mpv may use its mpv-gui to show video,
                # which causes the player crash.
                self.artwork_view.set_body(video_widget)
                video_widget.show()
        self.ctl_btns.hide()
        self.progress.hide()
        video_widget.ctl_bar.clear_adhoc_btns()
        exit_btn = video_widget.ctl_bar.add_adhoc_btn('退出视频模式')
        fullwindow_btn = video_widget.ctl_bar.add_adhoc_btn('窗口全屏')
        exit_btn.clicked.connect(self.unkeep_and_enter_cover_mode)
        fullwindow_btn.clicked.connect(
            lambda: self._app.watch_mgr.
            enter_fullwindow_mode(go_back=self.enter_video_mode)
        )

    def enter_cover_mode(self):
        self.artwork_view.set_body(None)
        self.ctl_btns.show()
        self.progress.show()

    def showEvent(self, a0) -> None:
        # When self is hidden, mpv_widget may be moved to somewhere else.
        # If it is removed, enter cover mode.
        if (
            self._app.ui.mpv_widget.parent() != self.artwork_view
            or self._app.player.video_format is None
        ):
            self.enter_cover_mode()
        else:
            self.enter_video_mode()
        return super().showEvent(a0)

    def sizeHint(self):
        return QSize(500, 400)

    def on_media_loaded(self, properties):
        if bool(properties['video_format']) is True:
            if self._keep_video_mode:
                self.enter_video_mode()
        else:
            self.enter_cover_mode()


class NowplayingOverlay(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.installEventFilter(self)

        self._splitter = QSplitter(self)
        self.player_panel = PlayerPanel(app, parent=self)
        self.stacked_widget = QStackedWidget(parent=self)
        self.tabbar = QTabBar(self)

        self.lyric_view = NowplayingLyricView(app)
        self.comments_view = NowplayingCommentListView(app)
        self.player_playlist_view = NowplayingPlayerPlaylistView(app)
        self.similar_songs_view = NowplayingSimilarSongsView(app)
        self.tabbar.addTab('歌词')
        self.tabbar.addTab('热门评论')
        self.tabbar.addTab('相似歌曲')
        self.tabbar.addTab('播放队列')
        self.stacked_widget.addWidget(self.lyric_view)
        self.stacked_widget.addWidget(self.comments_view)
        self.stacked_widget.addWidget(self.similar_songs_view)
        self.stacked_widget.addWidget(self.player_playlist_view)
        self.stacked_widget.setCurrentIndex(0)

        esc_hide_widget(self)
        self.tabbar.currentChanged.connect(self.stacked_widget.setCurrentIndex)
        self._layout = QHBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        set_default_font_families(self.comments_view)
        self.tabbar.setDocumentMode(True)
        self.tabbar.setShape(QTabBar.TriangularEast)
        self.setAutoFillBackground(True)
        self.lyric_view.viewport().setAutoFillBackground(False)
        self.comments_view.viewport().setAutoFillBackground(False)
        self.player_playlist_view.viewport().setAutoFillBackground(False)
        self.similar_songs_view.viewport().setAutoFillBackground(False)

        # Set contents margin explicitly.
        self._splitter.setHandleWidth(0)
        self._splitter.addWidget(self.player_panel)
        self._splitter.addWidget(self.stacked_widget)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.addWidget(self._splitter)
        self._layout.addWidget(self.tabbar)

    def showEvent(self, e):
        self.resize(self._app.size())
        super().showEvent(e)

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False


if __name__ == '__main__':
    from PyQt5.QtWidgets import QWidget

    from feeluown.gui.debug import simple_layout, mock_app
    from feeluown.player import Metadata

    with simple_layout(theme='dark') as layout, mock_app() as app:
        app.playlist.list.return_value = []
        app.size.return_value = QSize(600, 400)
        widget = NowplayingOverlay(app, None)
        widget.resize(600, 400)
        widget.player_panel.title_label.on_metadata_changed(
            Metadata(title='我和我的祖国', artists=['王菲'])
        )
        layout.addWidget(widget)
