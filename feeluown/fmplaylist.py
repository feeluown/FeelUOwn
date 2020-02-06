import logging

from queue import Queue
from feeluown.player import Playlist

logger = logging.getLogger(__name__)


class FMPlaylist:
    def __init__(self, playlist: Playlist):
        """无限大小的缓存队列"""
        self._cache_songs = Queue()

        self._playlist = playlist

        self._playlist.eof_reached.connect(self._append_song_to_playlist)

        self.fetch_songs_func = None

        """每次fetch 至少有 3首歌被加入 cache_songs"""
        self.fetch_songs_min_num = 3

    def _append_song_to_playlist(self):
        """向playlist中添加一首歌 然后调用next"""
        if self._cache_songs.qsize() == 0:
            if self.fetch_songs_func == None:
                logger.warning("fetch_songs_func isn't initialized properly")
                return 
            else:
                self.fetch_songs_func()
        if self._playlist is not None:
            """必须保证_cache_songs中有数据"""
            self._playlist.fm_add(self.cache_songs)
        self._playlist.next()

    @property
    def cache_songs(self):
        return self._cache_songs

    @cache_songs.setter
    def cache_songs(self, song):
        if song is not None:
            self._cache_songs.put(song)

    @cache_songs.getter
    def cache_songs(self):
        if self._cache_songs.qsize() == 0:
            return None
        else:
            return self._cache_songs.get(block=False)
