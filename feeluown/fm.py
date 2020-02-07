import asyncio
import logging
from queue import deque

from fuocore.excs import ProviderIOError
from feeluown.player import PlaylistMode

logger = logging.getLogger(__name__)


class FM:
    """FM
    """

    def __init__(self, app):
        """
        :type app: feeluown.app.App
        """
        self._app = app

        # store songs that are going to be added to playlist
        self._queue = deque()
        self._activated = False
        self._is_fetching_songs = False
        self._fetch_songs_task_name = 'fm-fetch-songs'
        self._fetch_songs_func = None
        self._minimum_per_fetch = 3

    def activate(self, fetch_songs_func):
        """activate fm mode

        :param fetch_songs_func: func(minimum, *args, **kwargs): -> list
            please ensure that fetch_songs_func can receive keyword arguments,
            we may send some keyword args(such as timeout) in the future.
            If exception occured in fetch_songs_func, it should raise
            :class:`fuocore.excs.ProviderIOError`.
        """
        if self._activated is True:
            logger.warning('fm already actiavted')
            return
        self._fetch_songs_func = fetch_songs_func
        self._app.playlist.eof_reached.connect(self._on_playlist_eof_reached)
        self._app.playlist.mode = PlaylistMode.fm
        self._activated = True
        self._app.playlist.next()

    def deactivate(self):
        """deactivate fm mode"""
        if not self._activated:
            return
        try:
            self._app.playlist.eof_reached.connect(self._on_playlist_eof_reached)
        except TypeError:
            pass
        self._fetch_songs_func = None
        self._app.playlist.mode = PlaylistMode.normal
        self._activated = False

    def _on_playlist_eof_reached(self):
        if self._queue:
            self._feed_playlist()
            return

        if self._is_fetching_songs:
            return

        self._is_fetching_songs = True
        task_spec = self._app.task_mgr.get_or_create(self._fetch_songs_task_name)
        task = task_spec.bind_blocking_io(
            self._fetch_songs_func, self._minimum_per_fetch)
        task.add_done_callback(self._on_songs_fetched)

    def _feed_playlist(self):
        song = self._queue.popleft()
        self._app.playlist.fm_add(song)
        self._app.playlist.next()

    def _on_songs_fetched(self, future):
        try:
            songs = future.result()
        except asyncio.CancelledError:
            logger.exception('fm-fetch-songs task is cancelled')
        except ProviderIOError:
            logger.exception('fm-fetch-songs io error')
        else:
            for song in songs:
                self._queue.append(song)
            self._feed_playlist()
        finally:
            self._is_fetching_songs = False
