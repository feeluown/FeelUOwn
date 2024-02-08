from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import QEvent, QSize
from PyQt5.QtGui import QResizeEvent, QKeySequence
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QShortcut, QStackedLayout, QTabBar
)

from feeluown.gui.components.btns import MediaButtons
from feeluown.gui.components.nowplaying import (
    NowplayingArtwork,
    NowplayingLyricView,
    NowplayingCommentListView,
    NowplayingPlayerPlaylistView,
    NowplayingSimilarSongsView,
)
from feeluown.gui.components.line_song import TwoLineSongLabel
from feeluown.gui.helpers import set_default_font_families

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class StackedPanel(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)


class PlayerPanel(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self.artwork_label = NowplayingArtwork(app, self)
        self.title_label = TwoLineSongLabel(app, self)
        self.media_btns = MediaButtons(app, button_width=36, parent=self)

        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout(self)
        # Put the cover_label in a vboxlayout and add strech around it,
        # so that cover_label's sizehint is respected.
        self._layout.addWidget(self.title_label)
        self._layout.addSpacing(15)
        self._layout.addWidget(self.artwork_label)
        self._layout.addSpacing(15)
        self._layout.addWidget(self.media_btns)

    def sizeHint(self):
        return QSize(500, 400)


class NowplayingOverlay(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.installEventFilter(self)

        self.player_panel = PlayerPanel(app, parent=self)
        self.lyric_view = NowplayingLyricView(app, self)
        self.comments_view = NowplayingCommentListView(app, self)
        self.player_playlist_view = NowplayingPlayerPlaylistView(app, self)
        self.similar_songs_view = NowplayingSimilarSongsView(app, self)
        self.tabbar = QTabBar(self)
        self.tabbar.setDocumentMode(True)
        self.tabbar.setShape(QTabBar.TriangularEast)
        set_default_font_families(self.comments_view)

        self._layout = QHBoxLayout(self)
        self._stacked_layout = QStackedLayout()

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)
        self.tabbar.currentChanged.connect(self._stacked_layout.setCurrentIndex)
        self.setup_ui()

    def setup_ui(self):
        self.setAutoFillBackground(True)
        self.lyric_view.viewport().setAutoFillBackground(False)
        self.comments_view.viewport().setAutoFillBackground(False)
        self.player_playlist_view.viewport().setAutoFillBackground(False)
        self.similar_songs_view.viewport().setAutoFillBackground(False)

        self._layout.addWidget(self.player_panel)
        self._layout.addLayout(self._stacked_layout)
        self._layout.addWidget(self.tabbar)

        self.tabbar.addTab('歌词')
        self.tabbar.addTab('热门评论')
        self.tabbar.addTab('相似歌曲')
        self.tabbar.addTab('播放队列')
        self._stacked_layout.addWidget(self.lyric_view)
        self._stacked_layout.addWidget(self.comments_view)
        self._stacked_layout.addWidget(self.similar_songs_view)
        self._stacked_layout.addWidget(self.player_playlist_view)
        self._stacked_layout.setCurrentIndex(0)

    def showEvent(self, e):
        self.resize(self._app.size())
        super().showEvent(e)

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False


if __name__ == '__main__':
    import os
    from unittest.mock import Mock

    from PyQt5.QtCore import QDir
    from PyQt5.QtWidgets import QApplication, QWidget

    from feeluown.player import Metadata
    from feeluown.gui.theme import read_resource

    pkg_root_dir = os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')
    icons_dir = os.path.join(pkg_root_dir, 'gui/assets/icons')
    QDir.addSearchPath('icons', icons_dir)

    qss = read_resource('common.qss')
    dark = read_resource('dark.qss')
    qapp = QApplication([])
    app = Mock()
    app.size.return_value = QSize(600, 400)
    widget = NowplayingOverlay(app, None)
    widget.resize(600, 400)
    widget.setStyleSheet(qss + '\n' + dark)
    widget.player_panel.title_label.on_metadata_changed(
        Metadata(title='我和我的祖国', artists=['王菲'])
    )
    widget.show()
    qapp.exec()
