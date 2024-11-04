from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QDialog

from feeluown.utils.aio import run_afn
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
    SongMiniCardListDelegate,
)
from feeluown.utils.reader import create_reader


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class StandbyListOverlay(QDialog):
    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(parent=app, *args, **kwargs)

        self._app = app
        self.setAttribute(Qt.WA_DeleteOnClose);

        self._layout = QVBoxLayout(self)

        view_options = dict(row_height=60, no_scroll_v=False)
        view = SongMiniCardListView(**view_options)
        view.play_song_needed.connect(self._app.playlist.play_model)
        delegate = SongMiniCardListDelegate(
            view,
            card_min_width=self.width() - self.width()//6,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
        )
        view.setItemDelegate(delegate)
        self._view = view

        self.setup_ui()

    def setup_ui(self):
        self._layout.addWidget(self._view)

    def show_song(self, song):

        async def impl():
            results = await self._app.library.a_list_song_standby_v2(song)
            songs = [p[0] for p in results]
            self.show_songs(songs)

        self._app.task_mgr.run_afn_preemptive(impl, name='standby-list-overlay-show-song')

    def show_songs(self, songs):
        """
        """
        model = SongMiniCardListModel(
            create_reader(songs),
            fetch_cover_wrapper(self._app)
        )
        self._view.setModel(model)
