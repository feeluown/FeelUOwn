from feeluown.widgets.tabbar import Tab


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

    def on_tab_id_activated(self, tab_id):
        def cb():
            if tab_id != self.tab_id:
                self.show_by_tab_id(tab_id)
        return cb

    def show_by_tab_id(self, tab_id):
        raise NotImplementedError
