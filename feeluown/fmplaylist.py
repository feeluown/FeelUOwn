import logging

from queue import deque

logger = logging.getLogger(__name__)


class FMPlaylist:
    def __init__(self, app):
        """无限大小的缓存队列"""
        self._songs_cache = deque()
        """
        :type app: feeluown.app.App
        """
        self._app = app

        self._playlist = self._app.playlist

        self._playlist.eof_reached.connect(self._append_song_to_playlist)

        """fetch_songs_func(min_num=3)"""
        self.fetch_songs_func = None

    def _append_song_to_playlist(self):
        """向playlist中添加一首歌 然后调用next"""
        if self._songs_cache:
            if self.fetch_songs_func is None:
                logger.warning("fetch_songs_func isn't initialized properly")
                return
            """
            :type songs: list
            """
            songs = self.fetch_songs_func(min_num=3)
            if songs is not None:
                for song in songs:
                    self._songs_cache.append(song)
        if self._playlist is not None:
            """必须保证_songs_cache中有数据"""
            self._playlist.fm_add(self.pop_song_from_cache())
        else:
            logger.warning("self._playlist isn't initialized properly")
            return
        if self._songs_cache:
            self._playlist.next()

    def pop_song_from_cache(self):
        """从队列里弹出一首歌"""
        if self._songs_cache:
            return None
        else:
            return self._songs_cache.pop()
