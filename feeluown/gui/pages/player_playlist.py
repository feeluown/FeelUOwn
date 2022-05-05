from PyQt5.QtCore import Qt, QModelIndex

from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.gui.widgets import TextButton
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.widgets.songs import BaseSongsTableModel, Column, ColumnsMode


async def render(req, **kwargs):
    """/player_playlist handler
    """
    app = req.ctx['app']
    tab_name = req.query.get('tab_name', '')

    right_panel = app.ui.right_panel
    right_panel.set_body(right_panel.table_container)
    aio.create_task(
        app.ui.table_container.set_renderer(PlayerPlaylistRenderer(tab_name)))


class PlayerPlaylistRenderer(Renderer, TabBarRendererMixin):

    def __init__(self, tab_name):
        self.tabs = [
            # (title, tab_name, )
            ('播放列表', 'playlist', ),
            ('最近播放', 'recently_played', )
        ]
        self.tab_index = self._get_tabindex_by_tabname(tab_name) or 0

    async def render(self):
        self.meta_widget.title = self.tabs[self.tab_index][0]
        self.meta_widget.show()
        self.render_tab_bar()

        if self.tab_index == 0:
            await self.render_playlist()
        else:
            await self.render_recently_played()

    async def render_recently_played(self):
        songs = self._app.recently_played.list_songs()
        reader = create_reader(songs)
        self.show_songs(reader)
        self.toolbar.hide()

    async def render_playlist(self):
        self.songs_table.remove_song_func = self._app.playlist.remove
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        model = PlaylistTableModel(self._app.playlist, source_name_map)
        self.show_songs_by_model(model, columns_mode=ColumnsMode.playlist)

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

    def render_by_tab_index(self, tab_index):
        tab_name = self.tabs[tab_index][1]
        self._app.browser.goto(page='/player_playlist',
                               query={'tab_name': tab_name})

    def _get_tabindex_by_tabname(self, tab_name):
        for i, tab in enumerate(self.tabs):
            if tab[1] == tab_name:
                return i
        return 0


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
