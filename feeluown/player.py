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
        """如果歌曲 url 无效，则尝试从其它平台找一个替代品"""
        if song is None or \
           (song.meta.support_multi_quality and song.list_quality()) or \
           song.url:
            _Playlist.current_song.fset(self, song)
            return
        self.mark_as_bad(song)

        logger.info('song:%s is invalid, try to get standby', song)
        if self._task is not None:
            logger.info('try to cancel another find-song-standby task')
            self._task.cancel()
            self._task = None

        def _current_song_setter(task):
            nonlocal song
            try:
                songs = task.result()
            except asyncio.CancelledError:
                logger.debug('badsong-autoreplace task is cancelled')
            else:
                if songs:
                    # DOUBT: how Python closures works?
                    song = songs[0]
                _Playlist.current_song.fset(self, song)
            finally:
                self._task = None

        def fetch_in_bg():
            self._task = aio.create_task(self._app.library.a_list_song_standby(song))
            self._task.add_done_callback(_current_song_setter)

        call_soon(fetch_in_bg, self._loop)


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
