import asyncio
import random

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from feeluown.library import SongModel, BaseModel
from feeluown.models.uri import reverse
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.tabbar import TabBar
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
    SongMiniCardListDelegate,
)
from feeluown.utils import aio
from feeluown.utils.reader import create_reader


def acolor(s, a):
    """Create color with it's name and alpha"""
    color = QColor(s)
    color.setAlpha(a)
    return color


class PlaylistOverlay(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, parent=app, **kwargs)

        self._app = app
        self._scroll_area = QScrollArea(self)
        self._tabbar = TabBar(self)

        self._shadow_width = 15

        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._tabbar.setAutoFillBackground(True)
        self.setWindowFlags(Qt.SubWindow | Qt.CustomizeWindowHint)

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)
        QApplication.instance().focusChanged.connect(self.on_focus_changed)
        self._app.installEventFilter(self)
        self._tabbar.currentChanged.connect(self.on_tab_changed)
        self._tabbar.setCurrentIndex(0)
        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(self._shadow_width, 0, 0, 0)
        self._layout.setSpacing(0)

        self._h_layout = QHBoxLayout(self)

        self._tabbar.setDocumentMode(True)
        self._tabbar.addTab('播放列表')
        self._tabbar.addTab('最近播放')
        self._layout.addWidget(self._tabbar)
        self._layout.addLayout(self._h_layout)

        self._h_layout.addSpacing(0)
        self._h_layout.addWidget(self._scroll_area)

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        # Draw shadow effect on the left side.
        painter.save()
        shadow_width = self._shadow_width
        rect = QRect(0, 0, shadow_width, self.height())
        gradient = QLinearGradient(rect.topRight(), rect.topLeft())
        gradient.setColorAt(0, acolor('black', 70))
        gradient.setColorAt(0.05, acolor('black', 60))
        gradient.setColorAt(0.1, acolor('black', 30))
        gradient.setColorAt(0.2, acolor('black', 5))
        gradient.setColorAt(1, acolor('black', 0))
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

        # Draw a rect to fill the remain background.
        painter.setBrush(self.palette().color(QPalette.Base))
        painter.drawRect(shadow_width, 0, self.width()-shadow_width, self.height())

    def show(self):
        self.on_tab_changed(self._tabbar.currentIndex())
        super().show()

    def on_focus_changed(self, _, new):
        """
        Hide the widget when it loses focus.
        """
        if not self.isVisible():
            return
        # When the app is losing focus, the new is None.
        if new is None or new is self or new in self.findChildren(QWidget):
            return
        self.hide()

    def on_tab_changed(self, index):
        if index == 0:
            songs = self._app.playlist.list()
        else:
            songs = self._app.recently_played.list_songs()
        model = SongMiniCardListModel(
            create_reader(songs),
            fetch_cover_wrapper(self._app),
        )
        view = SongMiniCardListView(
            row_height=60,
            no_scroll_v=True,
            parent=self._scroll_area,
        )
        # TODO: spacing -> 4 items tuple
        view.setItemDelegate(SongMiniCardListDelegate(
            view,
            card_min_width=self.width() - self.width()//6,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
        ))
        view.setModel(model)
        self._scroll_area.setWidget(view)
        view.play_song_needed.connect(self._app.playlist.play_model)

    def eventFilter(self, obj, event):
        """
        Hide myself when the app is resized.
        """
        if obj is self._app and event.type() == QEvent.Resize:
            self.hide()
        return False
