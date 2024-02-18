import asyncio
import logging
import warnings
from abc import ABCMeta, abstractmethod
from enum import IntEnum

from feeluown.utils.dispatch import Signal
# some may import `Playlist` and `PlaybackMode` from player module
from feeluown.player.playlist import PlaybackMode, Playlist
from .metadata import Metadata

__all__ = ('Playlist',
           'AbstractPlayer',
           'PlaybackMode',
           'State',)

logger = logging.getLogger(__name__)


class State(IntEnum):
    """
    Player states.
    """
    stopped = 0
    #: 处于 paused 状态时，current_song 也可能为 False
    paused = 1
    playing = 2


class AbstractPlayer(metaclass=ABCMeta):
    """Player abstrace base class.

    Note that signals may be emitted from different thread. You should
    take care of race condition.
    """

    def __init__(self, _=None, **kwargs):
        """
        :param _: keep this arg to keep backward compatibility
        """
        self._position = 0  # seconds
        self._volume = 100  # (0, 100)
        self._playlist = None
        self._state = State.stopped
        self._duration = None

        self._current_media = None
        self._current_metadata = Metadata()
        self._video_format = None

        #: player position changed signal
        self.position_changed = Signal()
        self.seeked = Signal()

        #: player state changed signal
        self.state_changed = Signal()

        #: duration changed signal
        self.duration_changed = Signal()

        #: media about to change: (old_media, media)
        self.media_about_to_changed = Signal()
        self.media_changed = Signal()  # Media source is changed (not loaded yet).
        # The difference between media_loaded and media_loaded_v2 is that
        # media_loaded_v2 carries some media properties.
        self.media_loaded = Signal()  # Start to play the media.
        self.media_loaded_v2 = Signal()  # emit(properties)
        # Metadata is changed, and it may be changed during playing.
        self.metadata_changed = Signal()
        self.media_finished = Signal()  # Finish to play the media.
        self.media_loading_failed = Signal()

        #: volume changed signal: (int)
        self.volume_changed = Signal()

    @property
    def state(self):
        """Player state

        :rtype: State
        """
        return self._state

    @state.setter
    def state(self, value):
        """set player state, emit state changed signal

        outer object should not set state directly,
        use ``pause`` / ``resume`` / ``stop`` / ``play`` method instead.
        """
        self._state = value
        self.state_changed.emit(value)

    @property
    def current_media(self):
        return self._current_media

    @property
    def current_metadata(self) -> Metadata:
        """Metadata for the current media

        Check `MetadataFields` for all possible fields. Note that some fields
        can be missed if them are unknown. For example, a video's metadata
        may have no genre info.
        """
        return self._current_metadata

    @property
    def position(self):
        """player position, the units is seconds"""
        return self._position

    @position.setter
    def position(self, position):
        """set player position, the units is seconds"""

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        value = 0 if value < 0 else value
        value = 100 if value > 100 else value
        self._volume = value
        self.volume_changed.emit(value)

    @property
    def duration(self):
        """player media duration, the units is seconds"""
        return self._duration

    @duration.setter
    def duration(self, value):
        value = value or 0
        if value != self._duration:
            self._duration = value
            self.duration_changed.emit(value)

    @abstractmethod
    def play(self, media, video=True, metadata=None):
        """play media

        :param media: a local file absolute path, or a http url that refers to a
            media file
        :param video: show video or not
        :param metadata: metadata for the media
        """

    @abstractmethod
    def set_play_range(self, start=None, end=None):
        pass

    @abstractmethod
    def resume(self):
        """play playback"""

    @abstractmethod
    def pause(self):
        """pause player"""

    @abstractmethod
    def toggle(self):
        """toggle player state"""

    @abstractmethod
    def stop(self):
        """stop player"""

    @abstractmethod
    def shutdown(self):
        """shutdown player, do some clean up here"""

    # ------------------
    # Deprecated methods
    # ------------------
    @property
    def playlist(self):
        """(DEPRECATED) player playlist

        Player SHOULD not know the existence of playlist. However, in the
        very beginning, the player depends on playlist and listen playlist's
        signal. Other programs may depends on the playlist property and
        we keep it for backward compatibility.

        TODO: maybe add a DeprecationWarning in v3.8.

        :return: :class:`.Playlist`
        """
        return self._playlist

    def set_playlist(self, playlist):
        self._playlist = playlist

    @property
    def current_song(self):
        """(Deprecated) alias of playlist.current_song

        Please use playlist.current_song instead.
        """
        warnings.warn('use playlist.current_model instead', DeprecationWarning)
        return self._playlist.current_song

    def load_song(self, song) -> asyncio.Task:
        """加载歌曲

        如果目标歌曲与当前歌曲不相同，则修改播放列表当前歌曲，
        播放列表会发出 song_changed 信号，player 监听到信号后调用 play 方法，
        到那时才会真正的播放新的歌曲。如果和当前播放歌曲相同，则忽略。

        .. note::

            调用方应该直接调用 playlist.current_song = song 来切换歌曲
        """
        assert song is not None
        warnings.warn(
            'use playlist.set_current_model instead, this will be removed in v3.8',
            DeprecationWarning
        )
        return self._playlist.set_current_song(song)

    def play_song(self, song):
        """加载并播放指定歌曲"""
        warnings.warn(
            'use playlist.set_current_model instead, this will be removed in v3.8',
            DeprecationWarning
        )
        return self._playlist.set_current_song(song)

    def play_songs(self, songs):
        """(alpha) play list of songs"""
        warnings.warn(
            'use playlist.init_from instead, this will be removed in v3.8',
            DeprecationWarning
        )
        self.playlist.set_models(songs, next_=True)
