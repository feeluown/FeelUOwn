import copy
import logging
import random
from enum import IntEnum

from fuocore.dispatch import Signal
from fuocore.media import Media
from fuocore.utils import DedupList

logger = logging.getLogger(__name__)


class PlaybackMode(IntEnum):
    """
    Playlist playback mode.
    """
    one_loop = 0  #: One Loop
    sequential = 1  #: Sequential
    loop = 2  #: Loop
    random = 3  #: Random


class PlaylistV2:
    """player playlist provide a list of media/song/video to play
    """

    def __init__(self, items=None, playback_mode=PlaybackMode.loop,
                 audio_select_policy='hq<>'):
        self._playback_mode = playback_mode
        self._current_item = None
        self._bad_items = DedupList()  #: items whose url is invalid
        self._items = DedupList(items or [])

        self.audio_select_policy = audio_select_policy

        self.playback_mode_changed = Signal()
        self.item_changed = Signal()
        """current item changed signal

        The player will play the item after it receive the signal,
        when item is None, the player will stop playback.
        """
        self.item_changed_v2 = Signal()
        """current item chagned signal, v2

        emit(item, media)
        """

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        """overload [] operator"""
        return self._items[index]

    def mark_as_bad(self, item):
        if item in self._items and item not in self._bad_items:
            self._bad_items.append(item)

    def add(self, item):
        if item in self._items:
            return
        self._items.append(item)
        logger.debug('Add %s to player playlist', item)

    def insert(self, item):
        if item in self._items:
            return
        if self._current_item is None:
            self._items.append(item)
        else:
            index = self._items.index(self._current_item)
            self._items.insert(index + 1, item)

    def remove(self, item):
        """Remove item from playlist. O(n)

        If item is current item, remove the item and play next. Otherwise,
        just remove it.
        """
        if item in self._items:
            if self._current_item is None:
                self._items.remove(item)
            elif item == self._current_item:
                next_item = self.next_item
                # 随机模式下或者歌单只剩一首歌曲，下一首可能和当前歌曲相同
                if next_item == self.current_item:
                    self.current_item = None
                    self._items.remove(item)
                    self.current_item = self.next_item
                else:
                    self.current_item = self.next_item
                    self._items.remove(item)
            else:
                self._items.remove(item)
            logger.debug('Remove {} from player playlist'.format(item))
        else:
            logger.debug('Remove failed: {} not in playlist'.format(item))

        if item in self._bad_items:
            self._bad_items.remove(item)

    def init_from(self, items):
        """(alpha) temporarily, should only called by player.play_items"""
        self.clear()
        # since we will call items.clear method during playlist clearing,
        # we need to deepcopy items object here.
        self._items = DedupList(copy.deepcopy(items))

    def clear(self):
        """remove all items from playlists"""
        if self.current_item is not None:
            self.current_item = None
        self._items.clear()
        self._bad_items.clear()

    def list(self):
        """get all items in playlists"""
        return self._items

    @property
    def current_item(self):
        """
        current playing item, return None if there is no current item
        """
        return self._current_item

    @current_item.setter
    def current_item(self, item):
        """设置当前歌曲，将歌曲加入到播放列表，并发出 item_changed 信号

        .. note::

            该方法理论上只应该被 Player 对象调用。
        """
        media = None
        if item is not None:
            media = self.prepare_media(item)
        self._set_current_item(item, media)

    def _set_current_item(self, item, media):
        if item is None:
            self._current_item = None
        else:
            # add it to playlist if item not in playlist
            if item in self._items:
                self._current_item = item
            else:
                self.insert(item)
                self._current_item = item

    def prepare_media(self, item):
        """prepare media data
        """
        if item.meta.support_multi_quality:
            media, quality = item.select_media(self.audio_select_policy)
        else:
            media = item.url  # maybe a empty string
        return Media(media) if media else None

    @property
    def playback_mode(self):
        return self._playback_mode

    @playback_mode.setter
    def playback_mode(self, playback_mode):
        self._playback_mode = playback_mode
        self.playback_mode_changed.emit(playback_mode)

    def _get_good_item(self, base=0, random_=False, direction=1, loop=True):
        """从播放列表中获取一首可以播放的歌曲

        :param base: base index
        :param random: random strategy or not
        :param direction: forward if > 0 else backword
        :param loop: regard the item list as a loop

        >>> pl = Playlist([1, 2, 3])
        >>> pl._get_good_item()
        1
        >>> pl._get_good_item(base=1)
        2
        >>> pl._bad_items = [2]
        >>> pl._get_good_item(base=1, direction=-1)
        1
        >>> pl._get_good_item(base=1)
        3
        >>> pl._bad_items = [1, 2, 3]
        >>> pl._get_good_item()
        """
        if not self._items or len(self._items) <= len(self._bad_items):
            logger.debug('No good item in playlist.')
            return None

        good_items = []
        if direction > 0:
            if loop is True:
                item_list = self._items[base:] + self._items[0:base]
            else:
                item_list = self._items[base:]
        else:
            if loop is True:
                item_list = self._items[base::-1] + self._items[:base:-1]
            else:
                item_list = self._items[base::-1]
        for item in item_list:
            if item not in self._bad_items:
                good_items.append(item)
        if not good_items:
            return None
        if random_:
            return random.choice(good_items)
        else:
            return good_items[0]

    @property
    def next_item(self):
        """next item for player, calculated based on playback_mode"""
        # 如果没有正在播放的歌曲，找列表里面第一首能播放的
        if self.current_item is None:
            return self._get_good_item()

        if self.playback_mode == PlaybackMode.random:
            next_item = self._get_good_item(random_=True)
        else:
            current_index = self._items.index(self.current_item)
            if current_index == len(self._items) - 1:
                if self.playback_mode in (PlaybackMode.loop, PlaybackMode.one_loop):
                    next_item = self._get_good_item()
                elif self.playback_mode == PlaybackMode.sequential:
                    next_item = None
            else:
                next_item = self._get_good_item(base=current_index+1, loop=False)
        return next_item

    @property
    def previous_item(self):
        """previous item for player to play

        NOTE: not the last played item
        """
        if self.current_item is None:
            return self._get_good_item(base=-1, direction=-1)

        if self.playback_mode == PlaybackMode.random:
            previous_item = self._get_good_item(direction=-1)
        else:
            current_index = self._items.index(self.current_item)
            previous_item = self._get_good_item(base=current_index - 1, direction=-1)
        return previous_item

    def next(self):
        """advance to the next item in playlist"""
        self.current_item = self.next_item

    def previous(self):
        """return to the previous item in playlist"""
        self.current_item = self.previous_item


class Playlist(PlaylistV2):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.song_changed = Signal()
        self.song_changed_v2 = Signal()

    @property
    def current_song(self):
        return self.current_item

    @current_song.setter
    def current_song(self, song):
        media = None
        if song is not None:
            media = self.prepare_media(song)
        self._set_current_item(song, media)
        self.song_changed.emit(song)
        self.song_changed_v2.emit(song, media)

    @PlaylistV2.current_item.setter
    def current_item(self, item):
        PlaylistV2.current_item.__set__(self, item)
        self.current_song = item

    @property
    def next_song(self):
        return self.next_item

    @property
    def previous_song(self):
        return self.previous_item
