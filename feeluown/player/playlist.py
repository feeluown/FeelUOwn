import asyncio
import warnings
import logging
import random
from enum import IntEnum, Enum
from typing import Optional, TYPE_CHECKING

from feeluown.excs import ProviderIOError
from feeluown.utils import aio
from feeluown.utils.aio import run_fn, run_afn
from feeluown.utils.dispatch import Signal
from feeluown.utils.utils import DedupList
from feeluown.player import Metadata, MetadataFields
from feeluown.library import (
    MediaNotFound, SongProtocol, ModelType, NotSupported, ResourceNotFound
)
from feeluown.media import Media
from feeluown.library import reverse

if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)


def _get_song_str(song):
    return f'{song.source}:{song.title_display} - {song.artists_name_display}'


class PlaybackMode(IntEnum):
    """
    Playlist playback mode.

    .. versiondeprecated:: 3.8.12
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


class Playlist:
    def __init__(self, app: 'App', songs=None, playback_mode=PlaybackMode.loop,
                 audio_select_policy='hq<>'):
        """
        :param songs: list of :class:`feeluown.library.SongModel`
        :param playback_mode: :class:`feeluown.player.PlaybackMode`
        """
        self._app = app

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

        self._t_scm = self._app.task_mgr.get_or_create('set-current-model')

        # .. versionadded:: 3.7.11
        #    The *songs_removed* and *songs_added* signal.
        self.songs_removed = Signal()  # (index, count)
        self.songs_added = Signal()  # (index, count)
        # .. versionadded:: 3.9.0
        #    The *play_model_handling* signal.
        self.play_model_handling = Signal()

        self._app.player.media_finished.connect(self._on_media_finished)

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
        warnings.warn(
            'use set_models instead, this will be removed in v3.8',
            DeprecationWarning
        )
        self.set_models(songs, fm=False)

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
            previous_song = self._get_good_song(direction=-1, random_=True)
        else:
            current_index = self._songs.index(self.current_song)
            previous_song = self._get_good_song(base=current_index - 1, direction=-1)
        return previous_song

    async def a_next(self):
        self.next()

    def next(self) -> Optional[asyncio.Task]:
        if self.next_song is None:
            self.eof_reached.emit()
            return None
        else:
            return self.set_current_song(self.next_song)

    def _on_media_finished(self):
        # Play next model when current media is finished.
        if self.playback_mode == PlaybackMode.one_loop:
            return self.set_current_song(self.current_song)
        else:
            self.next()

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
            self.pure_set_current_song(None, None, None)
            return None

        if self.mode is PlaylistMode.fm and song not in self._songs:
            self.mode = PlaylistMode.normal

        # FIXME(cosven): `current_song.setter` depends on app.task_mgr and app.library,
        # which make it hard to test.
        return self._t_scm.bind_coro(self.a_set_current_song(song))

    async def a_set_current_song(self, song):
        """Set the `song` as the current song.

        If the song is bad, then this will try to use a standby in Playlist.normal mode.
        """
        song_str = _get_song_str(song)

        target_song = song  # The song to be set.
        media = None        # The corresponding media to be set.

        try:
            media = await self._prepare_media(song)
        except MediaNotFound as e:
            if e.reason is MediaNotFound.Reason.check_children:
                await self.a_set_current_song_children(song)
                return

            logger.info(f'{song_str} has no valid media, mark it as bad')
            self.mark_as_bad(song)
        except ProviderIOError as e:
            # FIXME: This may cause infinite loop when the prepare media always fails
            logger.error(f'prepare media failed: {e}, try next song')
            run_afn(self.a_next)
            return
        except Exception as e:  # noqa
            # When the exception is unknown, we mark the song as bad.
            self._app.show_msg(f'prepare media failed due to unknown error: {e}')
            logger.exception('prepare media failed due to unknown error, '
                             'so we mark the song as a bad one')
            self.mark_as_bad(song)
        else:
            assert media, "media must not be empty"

        # The song has no media, try to find and use standby unless it is in fm mode.
        if media is None:
            # if mode is fm mode, do not find standby song, just skip the song.
            if self.mode is PlaylistMode.fm:
                run_afn(self.a_next)
                return
            target_song, media = await self.find_and_use_standby(song)

        metadata = await self._prepare_metadata_for_song(target_song)
        self.pure_set_current_song(target_song, media, metadata)

    async def a_set_current_song_children(self, song):
        song_str = _get_song_str(song)
        # TODO: maybe we can just add children to playlist?
        self._app.show_msg(f'{song_str} 的播放资源在孩子节点上，将孩子节点添加到播放列表')
        self.mark_as_bad(song)
        logger.info(f'{song_str} has children, replace the current playlist')
        song = await run_fn(self._app.library.song_upgrade, song)
        if song.children:
            self.batch_add(song.children)
            await self.a_set_current_song(song.children[0])
        else:
            run_afn(self.a_next)
        return

    async def find_and_use_standby(self, song):
        song_str = _get_song_str(song)
        self._app.show_msg(f'{song_str} is invalid, try to find standby')
        logger.info(f'try to find standby for {song_str}')
        standby_candidates = await self._app.library.a_list_song_standby_v2(
            song,
            self.audio_select_policy
        )
        if standby_candidates:
            standby, media = standby_candidates[0]
            msg = f'Song standby was found in {standby.source} ✅'
            logger.info(msg)
            self._app.show_msg(msg)
            # Insert the standby song after the song
            if song in self._songs and standby not in self._songs:
                index = self._songs.index(song)
                self._songs.insert(index + 1, standby)
                self.songs_added.emit(index + 1, 1)
            return standby, media

        msg = 'Song standby not found'
        logger.info(msg)
        self._app.show_msg(msg)
        return song, None

    def pure_set_current_song(self, song, media, metadata=None):
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

        if song is not None:
            if media is None:
                run_afn(self.a_next)
            else:
                # Note that the value of model v1 {}_display may be None.
                kwargs = {}
                if not self._app.has_gui:
                    kwargs['video'] = False
                # TODO: set artwork field
                self._app.player.play(media, metadata=metadata, **kwargs)
        else:
            self._app.player.stop()

    async def _prepare_metadata_for_song(self, song):
        metadata = Metadata({
            MetadataFields.uri: reverse(song),
            MetadataFields.source: song.source,
            MetadataFields.title: song.title_display or '',
            # The song.artists_name should return a list of strings
            MetadataFields.artists: [song.artists_name_display or ''],
            MetadataFields.album: song.album_name_display or '',
        })
        try:
            song = await aio.run_fn(self._app.library.song_upgrade, song)
        except (NotSupported, ResourceNotFound):
            return metadata
        except:  # noqa
            logger.exception(f"fetching song's meta failed, song:'{song.title_display}'")
            return metadata

        artwork = ''
        released = ''
        if song.album is not None:
            try:
                album = await aio.run_fn(self._app.library.album_upgrade, song.album)
            except (NotSupported, ResourceNotFound):
                pass
            except:  # noqa
                logger.warning(
                    f"fetching song's album meta failed, song:{song.title_display}")
            else:
                artwork = album.cover
                released = album.released
                # For model v1, the cover can be a Media object.
                # For example, in fuo_local plugin, the album.cover is a Media
                # object with url set to fuo://local/songs/{identifier}/data/cover.
                if isinstance(artwork, Media):
                    artwork = artwork.url

        # Try to use album meta first.
        if artwork and released:
            metadata[MetadataFields.artwork] = artwork
            metadata[MetadataFields.released] = released
        else:
            metadata[MetadataFields.artwork] = song.pic_url or artwork
            metadata[MetadataFields.released] = song.date or released
        return metadata

    async def _prepare_metadata_for_video(self, video):
        metadata = Metadata({
            # The value of model v1 title_display may be None.
            MetadataFields.title: video.title_display or '',
            MetadataFields.source: video.source,
            MetadataFields.uri: reverse(video),
        })
        try:
            video = await aio.run_fn(self._app.library.video_upgrade, video)
        except NotSupported as e:
            logger.warning(f"can't get cover of video due to {str(e)}")
        else:
            metadata[MetadataFields.artwork] = video.cover
        return metadata

    async def _prepare_media(self, song):
        task_spec = self._app.task_mgr.get_or_create('prepare-media')
        task_spec.disable_default_cb()
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

    def set_current_model(self, model):
        """
        .. versionadded: 3.7.13
        """
        if ModelType(model.meta.model_type) is ModelType.song:
            return self.set_current_song(model)
        if model is None:
            self._app.player.stop()
            return
        return self._t_scm.bind_coro(self.a_set_current_model(model))

    async def a_set_current_model(self, model):
        """
        TODO: handle when model is a song

        .. versionadded: 3.7.13
        """
        assert ModelType(model.meta.model_type) is ModelType.video, \
            "{model.meta.model_type} is not supported, expecting a video model, "

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
            metadata = await self._prepare_metadata_for_video(video)
            kwargs = {}
            if not self._app.has_gui:
                kwargs['video'] = False
            self._app.player.play(media, metadata=metadata, **kwargs)

    """
    Sync methods.

    Currently, playlist has both async and sync methods to keep backward
    compatibility. Sync methods will be replaced by async methods in the end.
    """
    def play_model(self, model):
        """Set current model and play it

        .. versionadded: 3.7.14
        """
        # Stop the player so that user know the action is working.
        self._app.player.stop()
        self.play_model_handling.emit()
        task = self.set_current_model(model)
        if task is not None:
            def cb(future):
                try:
                    future.result()
                except:  # noqa
                    logger.exception('play model failed')
                else:
                    self._app.player.resume()
                    logger.info(f'play a model ({model}) succeed')
            task.add_done_callback(cb)
