from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from feeluown.library import SongModel
from feeluown.models.uri import reverse
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
    SongMiniCardListDelegate,
)
from feeluown.utils import aio
from feeluown.utils.reader import create_reader


class PlaylistOverlay(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, parent=app, **kwargs)

        self._app = app
        self._scroll_area = QScrollArea(self)
        self._shadow_width = 15

        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self.setWindowFlags(Qt.SubWindow | Qt.CustomizeWindowHint)

        #self.setWidget(Inner(self))

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(self._shadow_width, 0, 0, 0)
        self._layout.setSpacing(0)
        self._tabbar = QTabBar(self)
        self._tabbar.setDocumentMode(True)
        self._tabbar.addTab('播放列表')
        self._tabbar.addTab('最近播放')
        self._layout.addWidget(self._tabbar)
        self._layout.addWidget(self._scroll_area)

        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)
        self._tabbar.currentChanged.connect(self.on_tab_changed)
        self._tabbar.setCurrentIndex(0)

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        painter.save()
        shadow_width = self._shadow_width
        rect = QRect(0, 0, shadow_width, self.height())
        gradient = QLinearGradient(rect.topRight(), rect.topLeft())
        # gradient.setColorAt(0, self.palette().color(QPalette.Window))
        # gradient.setColorAt(1, self.palette().color(QColor('white')))
        gradient.setColorAt(0, acolor('black', 70))
        gradient.setColorAt(0.05, acolor('black', 60))
        gradient.setColorAt(0.1, acolor('black', 30))
        gradient.setColorAt(0.2, acolor('black', 5))
        gradient.setColorAt(1, acolor('black', 0))
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

        painter.setBrush(self.palette().color(QPalette.Base))
        painter.drawRect(shadow_width, 0, self.width()-shadow_width, self.height())

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.hide()

    def on_tab_changed(self, index):
        if index == 0:
            model = SongMiniCardListModel(
                create_reader(self._app.playlist.list()),
                song_image_fetch_wrapper(self._app),
            )
            view = SongMiniCardListView(
                row_height=60,
                no_scroll_v=True,
            )
            view.setItemDelegate(SongMiniCardListDelegate(
                view,
                card_min_width=250,
                card_height=50,
                card_v_spacing=10,
            ))
            view.setModel(model)
            self._scroll_area.setWidget(view)
        else:
            self._scroll_area.setWidget(None)


def acolor(s, a):
    color = QColor(s)
    color.setAlpha(a)
    return color


def song_image_fetch_wrapper(app):
    async def fetch(song, cb):
        if not isinstance(song, SongModel):
            return None
        album = song.album
        if album is None:
            return None

        album_id = reverse(album)
        uid = album_id + '/cover'
        await fetch_cover_wrapper(app)(album, cb, uid)
    return fetch
