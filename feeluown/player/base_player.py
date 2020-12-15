import logging
from abc import ABCMeta, abstractmethod
from enum import IntEnum

from feeluown.utils.dispatch import Signal
# some may import `Playlist` and `PlaybackMode` from player module
from feeluown.player.playlist import PlaybackMode, Playlist

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

        #: current media finished signal
        self.media_finished = Signal()

        #: duration changed signal
        self.duration_changed = Signal()

        #: media about to change: (old_media, media)
        self.media_about_to_changed = Signal()
        #: media changed signal
        self.media_changed = Signal()

        #: volume changed signal: (int)
        self.volume_changed = Signal()

        self._playlist.song_changed_v2.connect(self._on_song_changed)
        self.media_finished.connect(self._on_media_finished)

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
        self.volume_changed.emit(value)

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
    def set_play_range(self, start=None, end=None):
        pass

    def load_song(self, song):
        """加载歌曲

        如果目标歌曲与当前歌曲不相同，则修改播放列表当前歌曲，
        播放列表会发出 song_changed 信号，player 监听到信号后调用 play 方法，
        到那时才会真正的播放新的歌曲。如果和当前播放歌曲相同，则忽略。

        .. note::

            调用方不应该直接调用 playlist.current_song = song 来切换歌曲
        """
        if song is not None and song != self.current_song:
            self._playlist.current_song = song

    def play_song(self, song):
        """加载并播放指定歌曲"""
        self.load_song(song)
        self.resume()

    def play_songs(self, songs):
        """(alpha) play list of songs"""
        self.playlist.init_from(songs)
        self.playlist.next()
        self.resume()

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

    def _on_song_changed(self, song, media):
        """播放列表 current_song 发生变化后的回调

        判断变化后的歌曲是否有效的，有效则播放，否则将它标记为无效歌曲。
        如果变化后的歌曲是 None，则停止播放。
        """
        if song is not None:
            if media is None:
                self._playlist.mark_as_bad(song)
                self._playlist.next()
            else:
                self.play(media)
        else:
            self.stop()

    def _on_media_finished(self):
        if self._playlist.playback_mode == PlaybackMode.one_loop:
            self.playlist.current_song = self.playlist.current_song
        else:
            self._playlist.next()
