from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout

from feeluown.models.uri import reverse
from feeluown.utils import aio
from feeluown.gui.widgets.cover_label import CoverLabelV2


async def render(req, **kwargs):
    app = req.ctx['app']
    song = req.ctx['model']
    view = SongExploreView(app=app)
    app.ui.right_panel.set_body(view)

    # show song album cover
    song = await aio.run_fn(app.library.song_upgrade, song)
    album = app.library.cast_model_to_v1(song.album)
    cover = await aio.run_fn(lambda: album.cover)
    await view.cover_label.show_cover(cover, reverse(album))


class HeaderLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setTextFormat(Qt.RichText)
        # Margin is same as playlist list view CoverSpacing
        self.setIndent(20)


class SongExploreView(QWidget):
    def __init__(self, app):
        super().__init__(parent=None)
        self._app = app

        self._left_con = QWidget(self)  #: left container
        self._right_con = QWidget(self)
        self._right_layout = QVBoxLayout(self._right_con)

        self.cover_label = CoverLabelV2(app=app)

        self._layout = QHBoxLayout(self)
        self._setup_ui()

    def _setup_ui(self):
        self._layout.setSpacing(0)

        self._layout.addWidget(self._left_con)
        self._layout.addWidget(self._right_con)

        self._right_layout.addWidget(self.cover_label)
        self._right_layout.addStretch(0)
