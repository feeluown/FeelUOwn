import asyncio
import logging
import random
from enum import IntEnum, Enum
from typing import Optional, TYPE_CHECKING
from threading import Lock

from feeluown.excs import ProviderIOError
from feeluown.utils import aio
from feeluown.utils.aio import run_fn, run_afn
from feeluown.utils.dispatch import Signal
from feeluown.utils.utils import DedupList
from feeluown.library import (
    MediaNotFound, SongModel, ModelType, VideoModel, ModelNotFound,
    BriefSongModel,
)
from feeluown.media import Media
from .metadata_assembler import MetadataAssembler

if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)

TASK_SET_CURRENT_MODEL = 'playlist.set_current_model'
TASK_PLAY_MODEL = 'playlist.play_model'
TASK_PREPARE_MEDIA = 'playlist.prepare_media'


class PlaybackMode(IntEnum):
    """
    Playlist playback mode.

    .. deprecated:: 3.8.12
        Please use PlaylistRepeatMode and PlaylistShuffleMode instead.
    """
    one_loop = 0  #: One Loop
    sequential = 1  #: Sequential
    loop = 2  #: Loop
    random = 3  #: Random


class PlaylistRepeatMode(Enum):
    none = 'none'
    one = 'one'
    all = 'all'


class PlaylistShuffleMode(Enum):
    """
    Windows and macOS has multiple shuffle modes.
    """
    off = 'off'
    songs = 'songs'


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


class PlaylistPlayModelStage(IntEnum):
    prepare_media = 10
    find_standby_by_mv = 20
    find_standby = 30
    prepare_metadata = 40
    load_media = 50


class Playlist:
    def __init__(self, app: 'App', songs=None, playback_mode=PlaybackMode.loop,
                 audio_select_policy='hq<>'):
        """
        :param songs: list of :class:`feeluown.library.SongModel`
        :param playback_mode: :class:`feeluown.player.PlaybackMode`
        """
        self._app = app
        self._metadata_mgr = MetadataAssembler(app)

        #: init playlist mode normal
        self._mode = PlaylistMode.normal

        #: playlist eof signal
        # playlist have no enough songs
        self.eof_reached = Signal()

        #: playlist mode changed signal
        self.mode_changed = Signal()
        #: playback mode before changed to fm mode
        self._normal_mode_playback_mode = playback_mode

        #: store value for ``current_song`` property
        self._current_song = None
        self._current_song_mv = None

        #: songs whose url is invalid
        self._bad_songs = DedupList()

        #: store value for ``songs`` property
        self._songs = DedupList(songs or [])
        # Acquire this lock before changing _current_song or _songs.
        # NOTE: some methods emit some signal while holding the lock,
        #   the signal handler should pay much attention to avoid deadlock.
        #   One thing is that the signal handler should not call any method
        #   that requires the lock!!!
        self._songs_lock = Lock()

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
        self.song_mv_changed = Signal()  # emit(song, mv)

        #: When watch mode is on, playlist try to play the mv/video of the song
        self.watch_mode = False

        # .. versionadded:: 3.7.11
        #    The *songs_removed* and *songs_added* signal.
        self.songs_removed = Signal()  # (index, count)
        self.songs_added = Signal()  # (index, count)
        # .. versionadded:: 3.9.0
        #    The *play_model_handling* signal.
        self.play_model_handling = Signal()
        # .. versionadded:: 4.1.7
        #    The *play_model_handling* signal.
        self.play_model_stage_changed = Signal()

        self._app.player.media_finished.connect(self._on_media_finished)
        self.song_changed.connect(self._on_song_changed)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        """set playlist mode"""
        if self._mode is not mode:
            # we should change _mode at the very end
            self._mode = mode
            if mode is PlaylistMode.fm:
                self._normal_mode_playback_mode = self.playback_mode
                self.playback_mode = PlaybackMode.sequential
            else:
                self.playback_mode = self._normal_mode_playback_mode
            self.mode_changed.emit(mode)
            logger.info('playlist mode changed to %s', mode)

    @property
    def repeat_mode(self):
        if self.playback_mode in (PlaybackMode.loop, PlaybackMode.random):
            return PlaylistRepeatMode.all
        elif self.playback_mode is PlaybackMode.one_loop:
            return PlaylistRepeatMode.one
        return PlaylistRepeatMode.none

    @repeat_mode.setter
    def repeat_mode(self, mode):
        if mode is PlaylistRepeatMode.all:
            if self.playback_mode not in (PlaybackMode.loop, PlaybackMode.random):
                self.playback_mode = PlaybackMode.loop
        elif mode is PlaylistRepeatMode.one:
            self.playback_mode = PlaybackMode.one_loop
        else:
            self.playback_mode = PlaybackMode.sequential

    @property
    def shuffle_mode(self):
        if self.playback_mode is PlaybackMode.random:
            return PlaylistShuffleMode.songs
        return PlaylistShuffleMode.off

    @shuffle_mode.setter
    def shuffle_mode(self, mode):
        if mode is PlaylistShuffleMode.songs:
            self.playback_mode = PlaybackMode.random
        else:
            self.playback_mode = PlaybackMode.loop

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
        """
        Requires: acquire `_songs_lock` before calling this method.
        """
        if song in self._songs:
            return
        self._songs.append(song)
        length = len(self._songs)
        self.songs_added.emit(length-1, 1)

    def set_models(self, models, next_=False, fm=False):
        """
        .. versionadded: v3.7.13
        """
        self.clear()
        self.batch_add(models)
        if fm is False:
            self.mode = PlaylistMode.normal
        else:
            self.mode = PlaylistMode.fm
        if next_ is True:
            self.next()

    def batch_add(self, models):
        """
        .. versionadded: v3.7.13
        """
        with self._songs_lock:
            start_index = len(self._songs)
            for model in models:
                self._songs.append(model)
            end_index = len(self._songs)
            self.songs_added.emit(start_index, end_index - start_index)

    def add(self, song):
        """add song to playlist

        Theoretically, when playlist is in FM mode, we should not
        change songs list manually(without ``fm_add`` method). However,
        when it happens, we exit FM mode.
        """
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        with self._songs_lock:
            self._add(song)

    def fm_add(self, song):
        with self._songs_lock:
            self._fm_add_no_lock(song)

    def _fm_add_no_lock(self, song):
        """
        Only for unittest and internal usage.
        """
        self._add(song)

    def insert_after_current_song(self, song):
        """Insert song after current song

        Requires: acquire `_songs_lock` before calling this method.

        When current song is none, the song is appended.
        """
        if song in self._songs:
            return
        if self._mode is PlaylistMode.fm:
            self.mode = PlaylistMode.normal
        if self._current_song is None:
            self._add(song)
        else:
            index = self._songs.index(self._current_song)
            self._songs.insert(index + 1, song)
            self.songs_added.emit(index + 1, 1)

    def remove_no_lock(self, song):
        try:
            index = self._songs.index(song)
        except ValueError:
            logger.debug('Remove failed: {} not in playlist'.format(song))
        else:
            if self._current_song is None:
                self._songs.remove(song)
            elif song == self._current_song:
                next_song = self._get_next_song_no_lock()
                # 随机模式下或者歌单只剩一首歌曲，下一首可能和当前歌曲相同
                if next_song == self.current_song:
                    # Should set current song immediately.
                    # Should not use set_current_song, because it is an async task.
                    self.set_current_song_none()
                    self._songs.remove(song)
                    new_next_song = self._get_next_song_no_lock()
                    self.set_existing_song_as_current_song(new_next_song)
                elif next_song is None and self.mode is PlaylistMode.fm:
                    # The caller should not remove the current song when it
                    # is the last song in fm mode.
                    logger.error("Can't remove the last song in fm mode, will play next")
                    self._next_no_lock()
                    return
                else:
                    self._songs.remove(song)
                    self.set_existing_song_as_current_song(next_song)
            else:
                self._songs.remove(song)
            self.songs_removed.emit(index, 1)
            logger.debug('Remove {} from player playlist'.format(song))
        if song in self._bad_songs:
            self._bad_songs.remove(song)

    def remove(self, song):
        """Remove song from playlist. O(n)

        If song is current song, remove the song and play next. Otherwise,
        just remove it.
        """
        with self._songs_lock:
            self.remove_no_lock(song)

    def _replace_song_no_lock(self, model, umodel):
        index = self._songs.index(model)
        self._songs.insert(index+1, umodel)
        self.songs_added.emit(index+1, 1)
        if self.current_song == model:
            self.set_current_song_none()
        self._songs.remove(model)
        self.songs_removed.emit(index, 1)

    def clear(self):
        """remove all songs from playlists"""
        with self._songs_lock:
            if self.current_song is not None:
                self.set_current_song_none()
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
        """Get a good song from playlist.

        Requires: acquire `_songs_lock` before calling this method.

        :param base: base index
        :param random_: random strategy or not
        :param direction: forward if > 0 else backward
        :param loop: regard the song list as a loop

        >>> from unittest import mock
        >>> pl = Playlist(mock.Mock(), [1, 2, 3])
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

    def _get_next_song_no_lock(self):
        """
        Requires: acquire `_songs_lock` before calling this method.
        """
        assert self._songs_lock.locked()

        if self.current_song is None:
            return self._get_good_song()

        if self.playback_mode == PlaybackMode.random:
            next_song = self._get_good_song(random_=True)
        else:
            current_index = self._songs.index(self.current_song)
            is_last_song = current_index == len(self._songs) - 1
            if is_last_song and self.playback_mode == PlaybackMode.sequential:
                next_song = None
            else:
                if is_last_song:
                    base_index = 0
                else:
                    base_index = current_index + 1
                loop = self.playback_mode != PlaybackMode.sequential
                next_song = self._get_good_song(base=base_index, loop=loop)
        return next_song

    @property
    def next_song(self):
        """next song for player, calculated based on playback_mode"""
        # 如果没有正在播放的歌曲，找列表里面第一首能播放的
        with self._songs_lock:
            return self._get_next_song_no_lock()

    def _get_previous_song_no_lock(self):
        if self.current_song is None:
            return self._get_good_song(base=-1, direction=-1)

        if self.playback_mode == PlaybackMode.random:
            previous_song = self._get_good_song(direction=-1, random_=True)
        else:
            current_index = self._songs.index(self.current_song)
            previous_song = self._get_good_song(base=current_index - 1, direction=-1)
        return previous_song

    @property
    def previous_song(self):
        """previous song for player to play

        NOTE: not the last played song
        """
        with self._songs_lock:
            return self._get_previous_song_no_lock()

    async def a_next(self):
        self.next()

    def _next_no_lock(self):
        """
        Requires: acquire `_songs_lock` before calling this method.
        Only for unittest and internal usage.
        """
        next_song = self._get_next_song_no_lock()
        if next_song is None:
            self.eof_reached.emit()
            return None
        return self.set_existing_song_as_current_song(next_song)

    def next(self) -> Optional[asyncio.Task]:
        """
        Why _songs_lock is needed? Think about the following scenario:

            [A, B, C, D] is the playlist, and the current song is B.

            Timeline    t1             t2              t3      t4
            User:      play_next                     play D
            Player:                next_song is C

            The expected song to play is D. So lock is needed here.
        """
        with self._songs_lock:
            return self._next_no_lock()

    def _on_media_finished(self):
        # Play next model when current media is finished.
        if self.playback_mode == PlaybackMode.one_loop:
            with self._songs_lock:
                return self.set_existing_song_as_current_song(self.current_song)
        else:
            self.next()

    def _on_song_changed(self, song):
        self._app.task_mgr.run_afn_preemptive(self._fetch_current_song_mv, song)

    async def _fetch_current_song_mv(self, song):
        if song is None:
            self._current_song_mv = None
        else:
            try:
                mv = await run_fn(self._app.library.song_get_mv, song)
            except ProviderIOError:
                logger.exception('get song mv info failed')
                self._current_song_mv = None
            else:
                self._current_song_mv = mv
        self.song_mv_changed.emit(song, self._current_song_mv)

    def previous(self) -> Optional[asyncio.Task]:
        """return to the previous song in playlist"""
        with self._songs_lock:
            song = self._get_previous_song_no_lock()
            return self.set_existing_song_as_current_song(song)

    @property
    def current_song(self) -> Optional[SongModel]:
        """Current song

        return None if there is no current song
        """
        return self._current_song

    @current_song.setter
    def current_song(self, song: Optional[SongModel]):
        self.set_current_song(song)

    @property
    def current_song_mv(self) -> Optional[VideoModel]:
        return self._current_song_mv

    async def a_set_current_song(self, song):
        """Set the `song` as the current song.

        If the song is bad, then this will try to use a standby in Playlist.normal mode.
        """
        if song is None:
            self.set_current_song_none()
            return None

        if self.mode is PlaylistMode.fm and song not in self._songs:
            self.mode = PlaylistMode.normal

        target_song = song  # The song to be set.
        media = None        # The corresponding media to be set.
        try:
            self.play_model_stage_changed.emit(PlaylistPlayModelStage.prepare_media)
            media = await self._app.task_mgr.run_afn_preemptive(
                self._prepare_media,
                song,
                name=TASK_PREPARE_MEDIA,
            )
        except MediaNotFound as e:
            if e.reason is MediaNotFound.Reason.check_children:
                await self.a_set_current_song_children(song)
                return
        except ProviderIOError as e:
            # FIXME: This may cause infinite loop when the prepare media always fails
            logger.error(f'prepare media failed: {e}, try next song')
            run_afn(self.a_next)
            return
        except Exception as e:  # noqa
            # When the exception is unknown, we mark the song as bad.
            self._app.show_msg(f'获取歌曲链接失败: {e}')
            logger.exception('prepare media failed due to unknown error')
        else:
            assert media, "media must not be empty"

        # The song has no media, try to find and use standby unless it is in fm mode.
        if media is None:
            if self._app.config.ENABLE_MV_AS_STANDBY:
                self.play_model_stage_changed.emit(
                    PlaylistPlayModelStage.find_standby_by_mv)
                media = await self._prepare_mv_media(song)

            if media:
                self._app.show_msg('使用音乐视频作为其播放资源 ✅')
            else:
                self._app.show_msg('未找到可用的音乐视频资源 🙁')
                logger.info(f"no media found for {song}, mark it as bad")
                self.mark_as_bad(song)
                self.play_model_stage_changed.emit(PlaylistPlayModelStage.find_standby)
                target_song, media = await self.find_and_use_standby(song)

        metadata = None
        if media is not None:
            self.play_model_stage_changed.emit(PlaylistPlayModelStage.prepare_metadata)
            metadata = await self._metadata_mgr.prepare_for_song(target_song)
        self.play_model_stage_changed.emit(PlaylistPlayModelStage.load_media)
        self.set_current_song_with_media(target_song, media, metadata)

    async def a_set_current_song_children(self, song):
        # TODO: maybe we can just add children to playlist?
        self._app.show_msg(f'{song} 的播放资源在孩子节点上，将孩子节点添加到播放列表')
        self.mark_as_bad(song)
        logger.info(f'{song} has children, replace the current playlist')
        song = await run_fn(self._app.library.song_upgrade, song)
        if song.children:
            self.batch_add(song.children)
            await self.a_set_current_song(song.children[0])
        else:
            run_afn(self.a_next)
        return

    async def find_and_use_standby(self, song):
        self._app.show_msg(f'{song} 无可用的播放资源, 尝试寻找备用歌曲...')
        logger.info(f'try to find standby from other providers for {song}')
        standby_candidates = await self._app.library.a_list_song_standby_v2(
            song,
            self.audio_select_policy
        )
        if standby_candidates:
            standby, media = standby_candidates[0]
            logger.info(f'song standby was found in {standby.source} ✅')
            self._app.show_msg(f'在 {standby.source} 平台找到 {song} 的备用歌曲 ✅')
            # Insert the standby song after the song
            # TODO: 或许这里可以优化一下？用 self.insert 函数？
            with self._songs_lock:
                if song in self._songs and standby not in self._songs:
                    index = self._songs.index(song)
                    self._songs.insert(index + 1, standby)
                    self.songs_added.emit(index + 1, 1)
            return standby, media

        logger.info(f'{song} song standby not found')
        self._app.show_msg(f'未找到 {song} 的备用歌曲')
        return song, None

    def set_current_song_with_media(self, song, media, metadata=None):
        if song is None:
            self.set_current_song_none()
            return
        # Add it to playlist if song not in playlist.
        with self._songs_lock:
            self.insert_after_current_song(song)
            self._current_song = song
            # TODO: 这里可能有点问题。比如 current_song 怎样和 media 保持一致呢？
            self.song_changed.emit(song)
            self.song_changed_v2.emit(song, media)
        if media is None:
            self._app.show_msg("没找到可用的播放链接，播放下一首...")
            run_afn(self.a_next)
        else:
            kwargs = {}
            if not self._app.has_gui:
                kwargs['video'] = False
            # TODO: set artwork field
            self._app.player.play(media, metadata=metadata, **kwargs)

    def set_current_song_none(self):
        """A special case of `set_current_song_with_media`."""
        self._current_song = None
        self.song_changed.emit(None)
        self.song_changed_v2.emit(None, None)
        self._app.player.stop()

    async def _prepare_media(self, song):
        if self.watch_mode is True:
            mv_media = await self._prepare_mv_media(song)
            if mv_media:
                return mv_media
            self._app.show_msg('未找到可用的歌曲视频资源')
        return await aio.run_fn(
            self._app.library.song_prepare_media, song, self.audio_select_policy,
        )

    async def _prepare_mv_media(self, song) -> Optional[Media]:
        try:
            mv_media = await run_fn(
                self._app.library.song_prepare_mv_media,
                song,
                self._app.config.VIDEO_SELECT_POLICY)
        except MediaNotFound:
            mv_media = None
        except Exception as e:  # noqa
            mv_media = None
            logger.exception(f'fail to get {song} mv: {e}')
        return mv_media

    async def a_set_current_model(self, model):
        """
        TODO: handle when model is a song

        .. versionadded: 3.7.13
        """
        if model is None:
            self._app.player.stop()
            return
        if isinstance(model, BriefSongModel):
            return await self.a_set_current_song(model)

        video = model
        try:
            media = await aio.run_fn(
                self._app.library.video_prepare_media,
                video,
                self._app.config.VIDEO_SELECT_POLICY
            )
        except MediaNotFound:
            self._app.show_msg('没有可用的播放链接')
        else:
            metadata = await self._metadata_mgr.prepare_for_video(video)
            kwargs = {}
            if not self._app.has_gui:
                kwargs['video'] = False
            self._app.player.play(media, metadata=metadata, **kwargs)

    async def a_play_model(self, model):
        """
        .. versionadded: 4.1.7
        """
        # Stop the player so that user know the action is working.
        self._app.player.stop()
        if model is None:
            return
        self.play_model_handling.emit()
        if ModelType(model.meta.model_type) is ModelType.song:
            fn = self.a_set_current_song
            upgrade_fn = self._app.library.song_upgrade
        else:
            fn = self.a_set_current_model
            upgrade_fn = self._app.library.video_upgrade

        try:
            # Try to upgrade the model.
            umodel = await aio.run_fn(upgrade_fn, model)
        except ModelNotFound:
            pass
        except Exception as e:  # noqa
            logger.exception(f'upgrade model({model}) failed')
            self._app.alert_mgr.on_exception(e)
        else:
            # Replace the brief model with the upgraded model
            # when user try to play a brief model that is already in the playlist.
            if isinstance(model, BriefSongModel) and not isinstance(model, SongModel):
                with self._songs_lock:
                    if model in self._songs:
                        self._replace_song_no_lock(model, umodel)
            model = umodel

        try:
            await self._app.task_mgr.run_afn_preemptive(
                fn, model, name=TASK_SET_CURRENT_MODEL
            )
        except:  # noqa
            logger.exception(f'play model({model}) failed')
        else:
            self._app.player.resume()
            logger.info(f'play a model ({model}) succeed')

    """
    Sync methods.

    Currently, playlist has both async and sync methods to keep backward
    compatibility. Sync methods will be replaced by async methods in the end.
    Sync methods just wrap the async method.
    """
    def play_model(self, model):
        """Set current model and play it

        .. versionadded: 3.7.14
        """
        self._app.task_mgr.run_afn_preemptive(
            self.a_play_model, model, name=TASK_PLAY_MODEL
        )

    def set_current_model(self, model) -> asyncio.Task:
        """
        .. versionadded: 3.7.13
        """
        return self._app.task_mgr.run_afn_preemptive(
            self.a_set_current_model, model, name=TASK_SET_CURRENT_MODEL,
        )

    def set_existing_song_as_current_song(self, song):
        """
        Requires: acquire `_songs_lock` before calling this method.
        """
        self._current_song = song
        return self.set_current_song(song)

    def set_current_song(self, song):
        """
        .. versionadded:: 3.7.11
           The method is added to replace current_song.setter.
        """
        return self._app.task_mgr.run_afn_preemptive(
            self.a_set_current_song, song, name=TASK_SET_CURRENT_MODEL
        )
