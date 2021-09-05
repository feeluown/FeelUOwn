import asyncio
import copy
import logging
import random
from enum import IntEnum
from typing import Optional

from feeluown.excs import ProviderIOError
from feeluown.utils.dispatch import Signal
from feeluown.utils.utils import DedupList
from feeluown.library.excs import MediaNotFound
from feeluown.library.model_protocol import SongProtocol

logger = logging.getLogger(__name__)


class PlaybackMode(IntEnum):
    """
    Playlist playback mode.
    """
    one_loop = 0  #: One Loop
    sequential = 1  #: Sequential
    loop = 2  #: Loop
    random = 3  #: Random


class PlaylistMode(IntEnum):
    """playlist mode

    **What is FM mode?**

    In FM mode, playlist's playback_mode is unchangeable, it will
    always be sequential. When playlist has no more song,
    the playlist hopes someone(we call it ``FM`` here) will:
    1. catch the ``eof_reached`` signal
    2. add news songs to playlist by using ``fm_add`` method

    **When will playlist exit FM mode?**

    If user manually play a song, playlist will exit FM mode, at the
    same time, playlist will:
    1. clear itself
    2. change to normal mode
    3. set current song to the song
    """
    normal = 0  #: Normal
    fm = 1  #: FM mode


class Playlist:
    def __init__(self, app, songs=None, playback_mode=PlaybackMode.loop,
                 audio_select_policy='hq<>'):
        """
        :param songs: list of :class:`feeluown.models.SongModel`
        :param playback_mode: :class:`feeluown.player.PlaybackMode`
        """
        self._app = app

        #: mainthread asyncio loop ref
        # We know that feeluown is a asyncio-app, and we can assume
        # that the playlist is inited in main thread.
        self._loop = asyncio.get_event_loop()

        #: init playlist mode normal
        self._mode = PlaylistMode.normal

        #: playlist eof signal
        # playlist have no enough songs
        self.eof_reached = Signal()

        #: playlist mode changed signal
        self.mode_changed = Signal()

        #: store value for ``current_song`` property
        self._current_song = None

        #: songs whose url is invalid
        self._bad_songs = DedupList()

        #: store value for ``songs`` property
        self._songs = DedupList(songs or [])

        self.audio_select_policy = audio_select_policy

        #: store value for ``playback_mode`` property
        self._playback_mode = playback_mode

        #: playback mode changed signal
        self.playback_mode_changed = Signal()
        self.song_changed = Signal()
        """current song changed signal

        The player will play the song after it receive the signal,
        when song is None, the player will stop playback.
        """
        self.song_changed_v2 = Signal()
        """current song chagned signal, v2

        emit(song, media)
        """

        #: When watch mode is on, playlist try to play the mv/video of the song
        self.watch_mode = False

        # .. versionadded:: 3.7.11
        #    The *songs_removed* and *songs_added* signal.
        self.songs_removed = Signal()  # (index, count)
        self.songs_added = Signal()  # (index, count)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        """set playlist mode"""
        if self._mode is not mode:
            if mode is PlaylistMode.fm:
                self.playback_mode = PlaybackMode.sequential
            # we should change _mode at the very end
            self._mode = mode
            self.mode_changed.emit(mode)
            logger.info('playlist mode changed to %s', mode)

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):
        """overload [] operator"""
        return self._songs[index]

    def mark_as_bad(self, song):
        if song in self._songs and song not in self._bad_songs:
            self._bad_songs.append(song)

    def is_bad(self, song):
        return song in self._bad_songs

    def _add(self, song):
        if song in self._songs:
            return
        self._songs.append(song)
        length = len(self._songs)
        self.songs_added.emit(length-1, 1)

    def add(self, song):
        """add song to playlist

        Theoretically, when playlist is in FM mode, we should not
        change songs list manually(without ``fm_add`` method). However,
        when it happens, we exit FM mode.
        """
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        self._add(song)

    def fm_add(self, song):
        self._add(song)

    def insert(self, song):
        """Insert song after current song

        When current song is none, the song is appended.
        """
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        if song in self._songs:
            return
        if self._current_song is None:
            self._add(song)
        else:
            index = self._songs.index(self._current_song)
            self._songs.insert(index + 1, song)
            self.songs_added.emit(index + 1, 1)

    def remove(self, song):
        """Remove song from playlist. O(n)

        If song is current song, remove the song and play next. Otherwise,
        just remove it.
        """
        try:
            index = self._songs.index(song)
        except ValueError:
            logger.debug('Remove failed: {} not in playlist'.format(song))
        else:
            if self._current_song is None:
                self._songs.remove(song)
            elif song == self._current_song:
                next_song = self.next_song
                # 随机模式下或者歌单只剩一首歌曲，下一首可能和当前歌曲相同
                if next_song == self.current_song:
                    self.current_song = None
                    self._songs.remove(song)
                    self.current_song = self.next_song
                else:
                    next_song = self.next_song
                    self._songs.remove(song)
                    self.current_song = next_song
            else:
                self._songs.remove(song)
            self.songs_removed.emit(index, 1)
            logger.debug('Remove {} from player playlist'.format(song))
        if song in self._bad_songs:
            self._bad_songs.remove(song)

    def init_from(self, songs):
        """
        THINKING: maybe we should rename this method or maybe we should
        change mode on application level

        We change playlistmode here because the `player.play_all` call this
        method. We should check if we need to exit fm mode in `play_xxx`.
        Currently, we have two play_xxx API: play_all and play_song.
        1. play_all -> init_from
        2. play_song -> current_song.setter

        (alpha) temporarily, should only called by player.play_songs
        """

        if self.mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        self.clear()
        # since we will call songs.clear method during playlist clearing,
        # we need to deepcopy songs object here.
        self._songs = DedupList(copy.deepcopy(songs))
        if self._songs:
            self.songs_added.emit(0, len(self._songs))

    def clear(self):
        """remove all songs from playlists"""
        if self.current_song is not None:
            self.current_song = None
        length = len(self._songs)
        self._songs.clear()
        if length > 0:
            self.songs_removed.emit(0, length)
        self._bad_songs.clear()

    def list(self):
        """Get all songs in playlists"""
        return self._songs

    @property
    def playback_mode(self):
        return self._playback_mode

    @playback_mode.setter
    def playback_mode(self, playback_mode):
        if self._mode is PlaylistMode.fm:
            if playback_mode is not PlaybackMode.sequential:
                logger.warning("can't set playback mode to others in fm mode")
                return
        self._playback_mode = playback_mode
        self.playback_mode_changed.emit(self.playback_mode)

    def _get_good_song(self, base=0, random_=False, direction=1, loop=True):
        """从播放列表中获取一首可以播放的歌曲

        :param base: base index
        :param random: random strategy or not
        :param direction: forward if > 0 else backward
        :param loop: regard the song list as a loop

        >>> pl = Playlist([1, 2, 3])
        >>> pl._get_good_song()
        1
        >>> pl._get_good_song(base=1)
        2
        >>> pl._bad_songs = [2]
        >>> pl._get_good_song(base=1, direction=-1)
        1
        >>> pl._get_good_song(base=1)
        3
        >>> pl._bad_songs = [1, 2, 3]
        >>> pl._get_good_song()
        """
        if not self._songs or len(self._songs) <= len(self._bad_songs):
            logger.debug('No good song in playlist.')
            return None

        good_songs = []
        if direction > 0:
            if loop is True:
                song_list = self._songs[base:] + self._songs[0:base]
            else:
                song_list = self._songs[base:]
        else:
            if loop is True:
                song_list = self._songs[base::-1] + self._songs[:base:-1]
            else:
                song_list = self._songs[base::-1]
        for song in song_list:
            if song not in self._bad_songs:
                good_songs.append(song)
        if not good_songs:
            return None
        if random_:
            return random.choice(good_songs)
        else:
            return good_songs[0]

    @property
    def next_song(self):
        """next song for player, calculated based on playback_mode"""
        # 如果没有正在播放的歌曲，找列表里面第一首能播放的
        if self.current_song is None:
            return self._get_good_song()

        if self.playback_mode == PlaybackMode.random:
            next_song = self._get_good_song(random_=True)
        else:
            current_index = self._songs.index(self.current_song)
            if current_index == len(self._songs) - 1:
                if self.playback_mode in (PlaybackMode.loop, PlaybackMode.one_loop):
                    next_song = self._get_good_song()
                elif self.playback_mode == PlaybackMode.sequential:
                    next_song = None
            else:
                next_song = self._get_good_song(base=current_index+1, loop=False)
        return next_song

    @property
    def previous_song(self):
        """previous song for player to play

        NOTE: not the last played song
        """
        if self.current_song is None:
            return self._get_good_song(base=-1, direction=-1)

        if self.playback_mode == PlaybackMode.random:
            previous_song = self._get_good_song(direction=-1)
        else:
            current_index = self._songs.index(self.current_song)
            previous_song = self._get_good_song(base=current_index - 1, direction=-1)
        return previous_song

    def next(self) -> Optional[asyncio.Task]:
        if self.next_song is None:
            self.eof_reached.emit()
            return None
        else:
            return self.set_current_song(self.next_song)

    def previous(self) -> Optional[asyncio.Task]:
        """return to the previous song in playlist"""
        return self.set_current_song(self.previous_song)

    @property
    def current_song(self) -> Optional[SongProtocol]:
        """Current song

        return None if there is no current song
        """
        return self._current_song

    @current_song.setter
    def current_song(self, song: Optional[SongProtocol]):
        self.set_current_song(song)

    def set_current_song(self, song) -> Optional[asyncio.Task]:
        """设置当前歌曲，将歌曲加入到播放列表，并发出 song_changed 信号

        .. note::

            该方法理论上只应该被 Player 对象调用。

        if song has not valid media, we find a replacement in other providers

        .. versionadded:: 3.7.11
           The method is added to replace current_song.setter.
        """
        if song is None:
            self.pure_set_current_song(None, None)
            return None

        if self.mode is PlaylistMode.fm and song not in self._songs:
            self.mode = PlaylistMode.normal

        # FIXME(cosven): `current_song.setter` depends on app.task_mgr and app.library,
        # which make it hard to test.
        task_spec = self._app.task_mgr.get_or_create('set-current-song')
        return task_spec.bind_coro(self.a_set_current_song(song))

    async def a_set_current_song(self, song):
        song_str = f'{song.source}:{song.title_display} - {song.artists_name_display}'

        try:
            media = await self._prepare_media(song)
        except MediaNotFound:
            logger.info(f'{song_str} has no valid media, mark it as bad')
            self.mark_as_bad(song)

            # if mode is fm mode, do not find standby song,
            # just skip the song
            if self.mode is not PlaylistMode.fm:
                self._app.show_msg(f'{song_str} is invalid, try to find standby')
                logger.info(f'try to find standby for {song_str}')
                standby_candidates = await self._app.library.a_list_song_standby_v2(
                    song,
                    self.audio_select_policy
                )
                if standby_candidates:
                    standby, media = standby_candidates[0]
                    self._app.show_msg(f'Song standby was found in {standby.source} ✅')
                    # Insert the standby song after the song
                    if song in self._songs and standby not in self._songs:
                        index = self._songs.index(song)
                        self._songs.insert(index + 1, standby)
                        self.songs_added.emit(index + 1, 1)
                    # NOTE: a_list_song_standby ensure that the song.url is not empty
                    # FIXME: maybe a_list_song_standby should return media directly
                    self.pure_set_current_song(standby, media)
                else:
                    self._app.show_msg('Song standby not found')
                    self.pure_set_current_song(song, None)
            else:
                self.next()
        except ProviderIOError as e:
            # FIXME: This may cause infinite loop when the prepare media always fails
            logger.error(f'prepare media failed: {e}, try next song')
            self.pure_set_current_song(song, None)
        except:  # noqa
            # When the exception is unknown, we mark the song as bad.
            logger.exception('prepare media failed due to unknown error, '
                             'so we mark the song as a bad one')
            self.mark_as_bad(song)
            self.next()
        else:
            assert media, "media must not be empty"
            self.pure_set_current_song(song, media)

    def pure_set_current_song(self, song, media):
        if song is None:
            self._current_song = None
        else:
            # add it to playlist if song not in playlist
            if song in self._songs:
                self._current_song = song
            else:
                self.insert(song)
                self._current_song = song
        self.song_changed.emit(song)
        self.song_changed_v2.emit(song, media)

    async def _prepare_media(self, song):
        task_spec = self._app.task_mgr.get_or_create('prepare-media')
        if self.watch_mode is True:
            try:
                mv_media = await task_spec.bind_blocking_io(
                    self._app.library.song_prepare_mv_media,
                    song,
                    self._app.config.VIDEO_SELECT_POLICY)
            except MediaNotFound:
                mv_media = None
                self._app.show_msg('No mv found')
            except Exception as e:  # noqa
                mv_media = None
                self._app.show_msg(f'Prepare mv media failed: {e}')
            if mv_media:
                return mv_media
        return await task_spec.bind_blocking_io(
            self._app.library.song_prepare_media, song, self.audio_select_policy)
