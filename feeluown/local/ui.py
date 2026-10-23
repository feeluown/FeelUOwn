from feeluown.utils.reader import wrap
from feeluown.gui.page_containers.table import Renderer


class LibraryRenderer(Renderer):
    def __init__(self, songs, albums, artists, videos):
        self.songs = songs
        self.albums = albums
        self.artists = artists
        self.videos = videos
        self.playlists = []

    async def render(self):
        self.meta_widget.show()
        self.tabbar.show()
        self.tabbar.library_mode()

        # render songs
        self.show_songs(reader=wrap(self.songs), show_count=True)

        # bind signals
        self.toolbar.filter_albums_needed.connect(
            lambda types: self.albums_table.model().filter_by_types(types))
        self.tabbar.show_songs_needed.connect(
            lambda: self.show_songs(reader=wrap(self.songs),
                                    show_count=True))
        self.tabbar.show_albums_needed.connect(lambda: self.show_albums(self.albums))
        self.tabbar.show_artists_needed.connect(lambda: self.show_artists(self.artists))
        self.tabbar.show_playlists_needed.connect(
            lambda: self.show_playlists(self.playlists))
        self.tabbar.show_videos_needed.connect(
            lambda: self.show_songs(reader=wrap(self.videos), show_count=True))
