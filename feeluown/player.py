# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
from functools import partial

from fuocore import aio
from fuocore.media import Media
from fuocore.player import MpvPlayer, Playlist as _Playlist


logger = logging.getLogger(__name__)


def call_soon(func, loop):
    if threading.current_thread() is threading.main_thread():
        func()
    else:
        loop.call_soon_threadsafe(func)


class Playlist(_Playlist):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        #: mainthread asyncio loop ref
        # We know that feeluown is a asyncio-app, and we can assume
        # that the playlist is inited in main thread.
        self._loop = asyncio.get_event_loop()

        #: find-song-standby task
        self._task = None

    @_Playlist.current_song.setter
    def current_song(self, song):
        """if song has not valid medai, we find a replacement in other providers"""

        def validate_song(song):
            # TODO: except specific exception
            valid_quality_list = []
            if song.meta.support_multi_quality:
                try:
                    valid_quality_list = song.list_quality()
                except:  # noqa
                    pass
            try:
                url = song.url
            except:  # noqa
                url = ''
            return bool(valid_quality_list or url)

        def find_song_standby_cb(task):
            final_song = song
            try:
                songs = task.result()
            except asyncio.CancelledError:
                logger.debug('badsong-autoreplace task is cancelled')
            else:
                if songs:
                    final_song = songs[0]
                    logger.info('find song standby success: %s', final_song)
                else:
                    logger.info('find song standby failed: not found')
                _Playlist.current_song.fset(self, final_song)

        def validate_song_cb(future):
            try:
                valid = future.result()
            except:  # noqa
                valid = False
            if valid:
                _Playlist.current_song.fset(self, song)
                return
            self.mark_as_bad(song)
            logger.info('song:%s is invalid, try to find standby', song)
            task_spec = self._app.task_mgr.get_or_create('find-song-standby')
            task = task_spec.bind_coro(self._app.library.a_list_song_standby(song))
            task.add_done_callback(find_song_standby_cb)

        if song is None:
            _Playlist.current_song.fset(self, song)
            return

        task_spec = self._app.task_mgr.get_or_create('validate-song')
        future = task_spec.bind_blocking_io(validate_song, song)
        future.add_done_callback(validate_song_cb)



class Player(MpvPlayer):

    def __init__(self, app, *args, **kwargs):
        super().__init__(playlist=Playlist(app), *args, **kwargs)
        self._app = app
        self._loop = asyncio.get_event_loop()
        self.initialize()

    def prepare_media(self, song, done_cb=None):
        def callback(future):
            try:
                media, quality = future.result()
            except Exception as e:
                logger.exception('prepare media data failed')
            else:
                media = Media(media) if media else None
                done_cb(media)

        if song.meta.support_multi_quality:
            fetch = partial(song.select_media, self._app.config.AUDIO_SELECT_POLICY)
        else:
            fetch = lambda: (song.url, None)

        def fetch_in_bg():
            future = self._loop.run_in_executor(None, fetch)
            future.add_done_callback(callback)

        call_soon(fetch_in_bg, self._loop)
