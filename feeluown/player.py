# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
from enum import IntEnum
from functools import partial

from fuocore.media import Media
from fuocore.player import MpvPlayer, Playlist as _Playlist
from fuocore.dispatch import Signal

logger = logging.getLogger(__name__)


def call_soon(func, loop):
    if threading.current_thread() is threading.main_thread():
        func()
    else:
        loop.call_soon_threadsafe(func)


class PlaylistMode(IntEnum):
    """
    Playlist  mode.
    """
    normal = 0  #: Normal
    personalFM = 1  #: FM mode


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
        self._playlist_mode = PlaylistMode.normal

        #: playlist eof signal
        # playlist have no enough songs
        self.playlist_eof = Signal()

    def add(self, song):
        """往播放列表末尾添加一首歌曲"""
        if self._playlist_mode is PlaylistMode.normal:
            super().add(song)
        elif self._playlist_mode is PlaylistMode.personalFM:
            self.playlist_mode = PlaylistMode.normal
            super().add(song)
            logger.warning("when personalFM,feeluown.Player.Playlist.add is a bug")

    def insert(self, song):
        """在当前歌曲后插入一首歌曲"""
        if self._playlist_mode is PlaylistMode.normal:
            super().insert(song)
        elif self._playlist_mode is PlaylistMode.personalFM:
            self.playlist_mode = PlaylistMode.normal
            super().insert(song)
            logger.warning("when personalFM,feeluown.Player.Playlist.insert is a bug")

    def remove(self, song):
        if self._playlist_mode is PlaylistMode.normal:
            super().remove(song)
        elif self._playlist_mode is PlaylistMode.personalFM:
            """还需要设计FMlist 这里需要重写 这里可能会触发eof信号"""
            if self._current_song is None:
                current_index = 0
            else:
                current_index = self._songs.index(self.current_song)
            if(len(self._songs) - current_index < 3):
                self.playlist_eof.emit()
            super().remove(song)
            logger.warning("when personalFM,feeluown.Player.Playlist.remove is a bug")

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

        if self._playlist_mode is PlaylistMode.personalFM:
            if song in self._songs:
                pass
            else:
                self.playlist_mode = PlaylistMode.normal

        if song is None:
            _Playlist.current_song.fset(self, song)
            return

        task_spec = self._app.task_mgr.get_or_create('validate-song')
        future = task_spec.bind_blocking_io(validate_song, song)
        future.add_done_callback(validate_song_cb)

    @_Playlist.playback_mode.setter
    def playback_mode(self, playback_mode):
        if self._playlist_mode is PlaylistMode.normal:
            _Playlist.playback_mode.fset(self, playback_mode)
        elif self._playlist_mode is PlaylistMode.personalFM:
            """需要确保此时playback_mode为 Sequential"""
            pass

    @property
    def playlist_mode(self):
        return self._playlist_mode

    @playlist_mode.setter
    def playlist_mode(self, playlist_mode):
        """切换mode成功需要清空playlist"""
        if self._playlist_mode is not playlist_mode:
            self._playlist_mode = playlist_mode
            self.clear()


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
            except Exception:  # noqa
                logger.exception('prepare media data failed')
            else:
                media = Media(media) if media else None
                done_cb(media)

        if song.meta.support_multi_quality:
            fetch = partial(song.select_media, self._app.config.AUDIO_SELECT_POLICY)
        else:
            fetch = lambda: (song.url, None)  # noqa

        def fetch_in_bg():
            future = self._loop.run_in_executor(None, fetch)
            future.add_done_callback(callback)

        call_soon(fetch_in_bg, self._loop)
