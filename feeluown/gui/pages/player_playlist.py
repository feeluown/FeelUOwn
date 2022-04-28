from PyQt5.QtCore import Qt, QModelIndex

from feeluown.utils import aio
from feeluown.gui.widgets import TextButton
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.widgets.songs import BaseSongsTableModel, Column


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

        self.songs_table.remove_song_func = self._app.playlist.remove
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = PlaylistTableModel(self._app.playlist, source_name_map)
        self.show_songs_by_model(model)

        # TODO(cosven): the toolbar is useless, and we should remove it lator.
        self.toolbar.manual_mode()
        btn = TextButton('清空', self.toolbar)
        btn.clicked.connect(lambda *args: aio.create_task(self.clear_playlist()))
        self.toolbar.add_tmp_button(btn)

        # Scroll to current song.
        current_song = self._app.playlist.current_song
        if current_song is not None:
            row = self._app.playlist.list().index(current_song)
            model_index = self.songs_table.model().index(row, Column.song)
            self.songs_table.scrollTo(model_index)
            self.songs_table.selectRow(row)

    async def clear_playlist(self):
        self._app.playlist.clear()
        await self.render()  # re-render


class PlaylistTableModel(BaseSongsTableModel):
    def __init__(self, playlist, source_name_map=None, parent=None):
        """

        :param songs: 歌曲列表
        :param songs_g: 歌曲列表生成器（当歌曲列表生成器不为 None 时，忽略 songs 参数）
        """
        super().__init__(source_name_map, parent)
        self._playlist = playlist
        self._items = playlist.list().copy()

        self._playlist.songs_added.connect(self.on_songs_added)
        self._playlist.songs_removed.connect(self.on_songs_removed)

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == Column.song:
            song = index.data(Qt.UserRole)
            if self._playlist.is_bad(song):
                # a bad song is disabled
                flags &= ~Qt.ItemIsEnabled
        return flags

    def on_songs_added(self, index, count):
        self.beginInsertRows(QModelIndex(), index, index+count-1)
        # Insert from tail to front.
        while count > 0:
            self._items.insert(index, self._playlist[index+count-1])
            count -= 1
        self.endInsertRows()

    def on_songs_removed(self, index, count):
        self.beginRemoveRows(QModelIndex(), index, index+count-1)
        while count > 0:
            self._items.pop(index + count - 1)
            count -= 1
        self.endRemoveRows()
