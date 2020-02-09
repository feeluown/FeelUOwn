# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
from enum import IntEnum
from functools import partial

from fuocore.media import Media
from fuocore.player import MpvPlayer, Playlist as _Playlist
from fuocore.playlist import PlaybackMode
from fuocore.dispatch import Signal

logger = logging.getLogger(__name__)


def call_soon(func, loop):
    if threading.current_thread() is threading.main_thread():
        func()
    else:
        loop.call_soon_threadsafe(func)


class PlaylistMode(IntEnum):
    """playlist mode

    **What is FM mode?**

    In FM mode, playlist's playback_mode is unchangable, it will
    always be sequential. When playlist has no more song,
    the playlist hopes someone(we call it ``FMPlaylist`` here) will:
    1. catch the ``eof_reached`` signal
    2. add news songs to playlist by using ``fm_add`` method
    3. call ``next`` method to resume the player

    **How to enter FM mode?**

    Only FMPlaylist can(should) make playlist enter FM mode, it should
    do following things:
    1. clear the playlist
    2. change playlist mode to FM
    3. add several songs to playlist
    4. resume the player with the first song

    **When will playlist exit FM mode?**

    If user manually play a song, playlist will exit FM mode, at the
    same time, playlist will:
    1. clear itself
    2. change to normal mode
    3. set current song to the song
    """
    normal = 0  #: Normal
    fm = 1  #: FM mode


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

        #: init playlist mode normal
        self._mode = PlaylistMode.normal

        #: playlist eof signal
        # playlist have no enough songs
        self.eof_reached = Signal()

        #: playlist mode changed signal
        self.mode_changed = Signal()

    def add(self, song):
        """add song to playlist

        Theoretically, when playlist is in FM mode, we should not
        change songs list manually(without ``fm_add`` method). However,
        when it happens, we exit FM mode.
        """
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        super().add(song)

    def insert(self, song):
        """insert song into playlist"""
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        super().insert(song)

    def fm_add(self, song):
        super().add(song)

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
                    logger.exception('[playlist] check song quality list failed')
            try:
                url = song.url
            except:  # noqa
                logger.exception('[playlist] get song url failed')
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
            self._app.show_msg('{} is invalid, try to find standby'.format(str(song)))
            task_spec = self._app.task_mgr.get_or_create('find-song-standby')
            task = task_spec.bind_coro(self._app.library.a_list_song_standby(song))
            task.add_done_callback(find_song_standby_cb)

        if song is None:
            _Playlist.current_song.fset(self, song)
            return

        if self.mode is PlaylistMode.fm and song not in self._songs:
            self.mode = PlaylistMode.normal

        task_spec = self._app.task_mgr.get_or_create('validate-song')
        future = task_spec.bind_blocking_io(validate_song, song)
        future.add_done_callback(validate_song_cb)

    @_Playlist.playback_mode.setter
    def playback_mode(self, playback_mode):
        if self._mode is PlaylistMode.fm:
            if playback_mode is not PlaybackMode.sequential:
                logger.warning("can't set playback mode to others in fm mode")
            else:
                _Playlist.playback_mode.fset(self, PlaybackMode.sequential)
        else:
            _Playlist.playback_mode.fset(self, playback_mode)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        """set playlist mode"""
        if self._mode is not mode:
            if mode is PlaylistMode.fm:
                self.playback_mode = PlaybackMode.sequential
            self.clear()
            # we should change _mode at the very end
            self._mode = mode
            self.mode_changed.emit(mode)
            logger.info('playlist mode changed to %s', mode)

    def next(self):
        if self.next_song is None:
            self.eof_reached.emit()
        else:
            super().next()


class Player(MpvPlayer):

    def __init__(self, app, *args, **kwargs):
        super().__init__(playlist=Playlist(app), *args, **kwargs)
        self._app = app
        self._loop = asyncio.get_event_loop()
        self.initialize()

    def play(self, url, video=True):
        if not (self._app.mode & self._app.GuiMode):
            video = False
        super().play(url, video)

    def prepare_media(self, song, done_cb=None):
        def callback(future):
            try:
                media, quality = future.result()
            except Exception:  # noqa
                logger.exception('prepare media data failed')
            else:
                media = Media(media) if media else None
                done_cb(media)

        if song.meta.support_multi_quality:
            fetch = partial(song.select_media, self._app.config.AUDIO_SELECT_POLICY)
        else:
            def fetch(): return (song.url, None)  # noqa

        def fetch_in_bg():
            future = self._loop.run_in_executor(None, fetch)
            future.add_done_callback(callback)

        call_soon(fetch_in_bg, self._loop)
