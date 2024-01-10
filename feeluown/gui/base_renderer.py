# mypy: disable-error-code=attr-defined
# HELP: No good way to type mixin class, see feeluown.gui.helpers docstring for details.

from abc import abstractmethod
from typing import runtime_checkable, Protocol

from feeluown.library import ModelType
from feeluown.gui.widgets.tabbar import Tab, TabBar


class LibraryTabRendererMixin:

    def init_tabbar_signal_binding(self):
        for tab_id, signal in self.get_tabid_signal_mapping().items():
            signal.connect(self.on_tab_id_activated(tab_id))

    def get_tabid_handler_mapping(self):
        return {
            Tab.songs: self.show_songs,
            Tab.albums: self.show_albums,
            Tab.artists: self.show_artists,
            Tab.playlists: self.show_playlists,
            Tab.videos: self.show_videos,
        }

    def get_tabid_signal_mapping(self):
        return {
            Tab.songs: self.tabbar.show_songs_needed,
            Tab.albums: self.tabbar.show_albums_needed,
            Tab.artists: self.tabbar.show_artists_needed,
            Tab.playlists: self.tabbar.show_playlists_needed,
            Tab.videos: self.tabbar.show_videos_needed,
        }

    def render_tabbar(self):
        self.init_tabbar_signal_binding()

        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(self.tab_id)

    def on_tab_id_activated(self, tab_id):
        def cb():
            if tab_id != self.tab_id:
                self.show_by_tab_id(tab_id)
        return cb

    def show_by_tab_id(self, tab_id):
        raise NotImplementedError


class TabBarRendererMixin:
    """
    Requirements:
    1. the instance MUST has `tabs` attribute
    2. the instance MUST implement `render_by_tab_index`
    """
    def render_tab_bar(self):
        tab_bar = TabBar()
        ui = self._app.ui
        ui.toolbar.add_stacked_widget(tab_bar)
        ui.toolbar.set_top_stacked_widget(tab_bar)
        for tab in self.tabs:
            tab_bar.addTab(tab[0])
        tab_bar.setCurrentIndex(self.tab_index)
        tab_bar.tabBarClicked.connect(self.render_by_tab_index)

    def render_by_tab_index(self, tab_index):
        raise NotImplementedError

    def default_tabs(self):
        return [
            ('歌曲', ModelType.song, self.show_songs),
            ('专辑', ModelType.album, self.show_albums),
            ('歌手', ModelType.artist, self.show_artists),
            ('歌单', ModelType.playlist, self.show_playlists),
            ('视频', ModelType.video, self.show_videos)
        ]


@runtime_checkable
class VFillableBg(Protocol):
    """Protocol for widgets which has vertical fillable background

    This protocol indicates the background of the widget is transparent. The parent
    widget can fill color for the widget.

    .. versionadded:: 3.8.9
    """
    @abstractmethod
    def fillable_bg_height(self) -> int:
        raise NotImplementedError
