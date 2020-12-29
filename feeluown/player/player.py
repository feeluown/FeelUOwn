# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
from enum import IntEnum

from feeluown.library.excs import MediaNotFound
from feeluown.player.mpvplayer import MpvPlayer
from feeluown.utils.dispatch import Signal
from .playlist import Playlist as _Playlist, PlaybackMode

logger = logging.getLogger(__name__)


def call_soon(func, loop):
    if threading.current_thread() is threading.main_thread():
        func()
    else:
        loop.call_soon_threadsafe(func)


class PlaylistMode(IntEnum):
    """playlist mode

    **What is FM mode?**

    In FM mode, playlist's playback_mode is unchangeable, it will
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
        """if song has not valid media, we find a replacement in other providers"""

        if song is None:
            self._set_current_song(None, None)
            return

        if self.mode is PlaylistMode.fm and song not in self._songs:
            self.mode = PlaylistMode.normal

        task_spec = self._app.task_mgr.get_or_create('set-current-song')
        task_spec.bind_coro(self.a_set_current_song(song))

    def init_from(self, songs):
        # THINKING: maybe we should rename this method or maybe we should
        # change mode on application level
        #
        # We change playlistmode here because the `player.play_all` call this
        # method. We should check if we need to exit fm mode in `play_xxx`.
        # Currently, we have two play_xxx API: play_all and play_song.
        # 1. play_all -> init_from
        # 2. play_song -> current_song.setter
        if self.mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        super().init_from(songs)

    async def a_set_current_song(self, song):
        task_spec = self._app.task_mgr.get_or_create('prepare-media')
        future = task_spec.bind_blocking_io(self.prepare_media, song)
        try:
            media = await future
        except MediaNotFound:
            media = None
        except:  # noqa
            logger.exception('prepare media failed')
            self.next()
            return
        if media is not None:
            self._set_current_song(song, media)
            return
        logger.info('song:{} media is None, mark as bad')
        self.mark_as_bad(song)

        # if mode is fm mode, do not find standby song,
        # just skip the song
        if self.mode is not PlaylistMode.fm:
            self._app.show_msg('{} is invalid, try to find standby'
                               .format(str(song)))

            songs = await self._app.library.a_list_song_standby(song)
            if songs:
                final_song = songs[0]
                logger.info('find song standby success: %s', final_song)
            else:
                logger.info('find song standby failed: not found')
                final_song = song
            self._set_current_song(final_song, final_song.url)
        else:
            self.next()

    @_Playlist.playback_mode.setter
    def playback_mode(self, playback_mode):
        if self._mode is PlaylistMode.fm:
            if playback_mode is not PlaybackMode.sequential:
                logger.warning("can't set playback mode to others in fm mode")
            else:
                _Playlist.playback_mode.__set__(self, PlaybackMode.sequential)
        else:
            _Playlist.playback_mode.__set__(self, playback_mode)

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

    def prepare_media(self, song):
        """prepare media data
        """
        return self._app.library.song_prepare_media(song, self.audio_select_policy)


class Player(MpvPlayer):

    def __init__(self, app, *args, **kwargs):
        playlist = Playlist(
            app,
            audio_select_policy=app.config.AUDIO_SELECT_POLICY)
        super().__init__(playlist=playlist, *args, **kwargs)
        self._app = app

    def play(self, url, video=True, **kwargs):
        if not (self._app.mode & self._app.GuiMode):
            video = False
        super().play(url, video, **kwargs)
