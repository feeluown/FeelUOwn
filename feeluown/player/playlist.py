import copy
import logging
import random
import warnings
from enum import IntEnum

from feeluown.utils.dispatch import Signal
from feeluown.media import Media
from feeluown.utils.utils import DedupList

logger = logging.getLogger(__name__)


class PlaybackMode(IntEnum):
    """
    Playlist playback mode.
    """
    one_loop = 0  #: One Loop
    sequential = 1  #: Sequential
    loop = 2  #: Loop
    random = 3  #: Random


class Playlist:
    """player playlist provide a list of song model to play
    """

    def __init__(self, songs=None, playback_mode=PlaybackMode.loop,
                 audio_select_policy='hq<>'):
        """
        :param songs: list of :class:`feeluown.models.SongModel`
        :param playback_mode: :class:`feeluown.player.PlaybackMode`
        """
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

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):
        """overload [] operator"""
        return self._songs[index]

    def mark_as_bad(self, song):
        if song in self._songs and song not in self._bad_songs:
            self._bad_songs.append(song)

    def add(self, song):
        """往播放列表末尾添加一首歌曲"""
        if song in self._songs:
            return
        self._songs.append(song)
        logger.debug('Add %s to player playlist', song)

    def insert(self, song):
        """在当前歌曲后插入一首歌曲"""
        if song in self._songs:
            return
        if self._current_song is None:
            self._songs.append(song)
        else:
            index = self._songs.index(self._current_song)
            self._songs.insert(index + 1, song)

    def remove(self, song):
        """Remove song from playlist. O(n)

        If song is current song, remove the song and play next. Otherwise,
        just remove it.
        """
        if song in self._songs:
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
                    self.current_song = self.next_song
                    self._songs.remove(song)
            else:
                self._songs.remove(song)
            logger.debug('Remove {} from player playlist'.format(song))
        else:
            logger.debug('Remove failed: {} not in playlist'.format(song))

        if song in self._bad_songs:
            self._bad_songs.remove(song)

    def init_from(self, songs):
        """(alpha) temporarily, should only called by player.play_songs"""
        self.clear()
        # since we will call songs.clear method during playlist clearing,
        # we need to deepcopy songs object here.
        self._songs = DedupList(copy.deepcopy(songs))

    def clear(self):
        """remove all songs from playlists"""
        if self.current_song is not None:
            self.current_song = None
        self._songs.clear()
        self._bad_songs.clear()

    def list(self):
        """get all songs in playlists"""
        return self._songs

    @property
    def current_song(self):
        """
        current playing song, return None if there is no current song
        """
        return self._current_song

    @current_song.setter
    def current_song(self, song):
        """设置当前歌曲，将歌曲加入到播放列表，并发出 song_changed 信号

        .. note::

            该方法理论上只应该被 Player 对象调用。
        """
        media = None
        if song is not None:
            media = self.prepare_media(song)
        self._set_current_song(song, media)

    def _set_current_song(self, song, media):
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

    def prepare_media(self, song):
        """prepare media data
        """
        warnings.warn('use library.song_prepare_media please', DeprecationWarning)
        if song.meta.support_multi_quality:
            media, quality = song.select_media(self.audio_select_policy)
        else:
            media = song.url  # maybe a empty string
        return Media(media) if media else None

    @property
    def playback_mode(self):
        return self._playback_mode

    @playback_mode.setter
    def playback_mode(self, playback_mode):
        self._playback_mode = playback_mode
        self.playback_mode_changed.emit(playback_mode)

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

    def next(self):
        """advance to the next song in playlist"""
        self.current_song = self.next_song

    def previous(self):
        """return to the previous song in playlist"""
        self.current_song = self.previous_song
