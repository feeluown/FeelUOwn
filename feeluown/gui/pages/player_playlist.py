from PyQt5.QtCore import Qt

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.widgets import TextButton
from feeluown.gui.helpers import disconnect_slots_if_has
from feeluown.gui.page_containers.table import Renderer
from feeluown.widgets.songs import SongsTableModel, Column, SongFilterProxyModel


async def render(req, **kwargs):
    """/player_playlist handler
    """
    app = req.ctx['app']

    right_panel = app.ui.right_panel
    right_panel.set_body(right_panel.table_container)
    aio.create_task(app.ui.table_container.set_renderer(PlayerPlaylistRenderer()))


class PlayerPlaylistRenderer(Renderer):

    async def render(self):
        self.meta_widget.title = '当前播放列表'
        self.meta_widget.show()

        self.container.current_table = self.songs_table
        self.songs_table.remove_song_func = self._app.playlist.remove
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = PlaylistTableModel(source_name_map, self._app.playlist)
        filter_model = SongFilterProxyModel(self.songs_table)
        filter_model.setSourceModel(model)
        self.songs_table.setModel(filter_model)
        disconnect_slots_if_has(self._app.ui.magicbox.filter_text_changed)
        self._app.ui.magicbox.filter_text_changed.connect(filter_model.filter_by_text)

        self.toolbar.show()
        btn = TextButton('清空', self.toolbar)
        btn.clicked.connect(lambda *args: aio.create_task(self.clear_playlist()))
        self.toolbar.add_tmp_button(btn)

        # scroll to current song
        current_song = self._app.playlist.current_song
        if current_song is not None:
            row = self._app.playlist.list().index(current_song)
            model_index = self.songs_table.model().index(row, Column.song)
            self.songs_table.scrollTo(model_index)
            self.songs_table.selectRow(row)

    async def clear_playlist(self):
        self._app.playlist.clear()
        await self.render()  # re-render


class PlaylistTableModel(SongsTableModel):
    def __init__(self, source_name_map, playlist):
        reader = wrap(playlist.list())
        super().__init__(source_name_map, reader)
        self._playlist = playlist

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == Column.song:
            song = index.data(Qt.UserRole)
            if self._playlist.is_bad(song):
                # a bad song is disabled
                flags &= ~Qt.ItemIsEnabled
        return flags
