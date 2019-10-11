import logging
from abc import ABCMeta, abstractmethod
from enum import IntEnum

from fuocore.dispatch import Signal
# some may import `Playlist` and `PlaybackMode` from player module
from fuocore.playlist import PlaybackMode, Playlist

__all__ = ('Playlist',
           'MpvPlayer',
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
    """Player abstrace base class"""

    def __init__(self, playlist=None, **kwargs):
        self._position = 0  # seconds
        self._volume = 100  # (0, 100)
        self._playlist = Playlist() if playlist is None else playlist
        self._state = State.stopped
        self._duration = None

        self._current_media = None

        #: player position changed signal
        self.position_changed = Signal()

        #: player state changed signal
        self.state_changed = Signal()

        #: current song finished signal
        self.song_finished = Signal()

        #: duration changed signal
        self.duration_changed = Signal()

        #: media changed signal
        self.media_changed = Signal()

    @property
    def state(self):
        """Player state

        :return: :class:`.State`
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
    def current_song(self):
        """alias of playlist.current_song"""
        return self._playlist.current_song

    @property
    def playlist(self):
        """player playlist

        :return: :class:`.Playlist`
        """
        return self._playlist

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

    @property
    def duration(self):
        """player media duration, the units is seconds"""
        return self._duration

    @duration.setter
    def duration(self, value):
        if value is not None and value != self._duration:
            self._duration = value
            self.duration_changed.emit(value)

    @abstractmethod
    def play(self, url, video=True):
        """play media

        :param url: a local file absolute path, or a http url that refers to a
            media file
        :param video: show video or not
        """

    @abstractmethod
    def prepare_media(self, song, done_cb=None):
        """prepare media data

        In practice, we usually need to perform some web requests to extract
        media data from song object, which may block the whole thread.
        We can override this method to make the request action non-blocking,
        when the action finishes, invoke done callback.

        :param song: SongModel instance
        :param done_cb: prepare done callback
        """

    @abstractmethod
    def play_song(self, song):
        """play media by song model

        :param song: :class:`fuocore.models.SongModel`
        """

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
    def initialize(self):
        """"initialize player"""

    @abstractmethod
    def shutdown(self):
        """shutdown player, do some clean up here"""


# FIXME: remove this when no one import MpvPlayer from here
from fuocore.mpvplayer import MpvPlayer  # noqa: F841, F401
