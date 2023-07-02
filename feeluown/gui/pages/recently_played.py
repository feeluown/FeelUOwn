from PyQt5.QtCore import Qt, QModelIndex

from feeluown.utils.aio import run_afn
from feeluown.utils.reader import create_reader
from feeluown.gui.widgets import TextButton
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.widgets.songs import BaseSongsTableModel, Column, ColumnsMode


async def render(req, **kwargs):
    app = req.ctx['app']
    right_panel = app.ui.right_panel
    right_panel.set_body(right_panel.table_container)
    run_afn(app.ui.table_container.set_renderer, PlayerPlaylistRenderer())


class PlayerPlaylistRenderer(Renderer):

    async def render(self):
        self.meta_widget.title = '最近播放'
        self.meta_widget.show()
        songs = self._app.recently_played.list_songs()
        reader = create_reader(songs)
        self.show_songs(reader)
        self.toolbar.hide()
