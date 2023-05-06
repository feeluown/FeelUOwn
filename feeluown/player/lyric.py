from __future__ import annotations
import re
import logging
from typing import Dict, Optional, TYPE_CHECKING
from collections import namedtuple, OrderedDict

from feeluown.library import LyricModel, NotSupported
from feeluown.utils import aio
from feeluown.utils.dispatch import Signal

if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)


def find_previous(element, list_):
    """
    find previous element in a sorted list

    >>> find_previous(0, [0])
    (0, 0)
    >>> find_previous(2, [1, 1, 3])
    (1, 1)
    >>> find_previous(0, [1, 2])
    (None, None)
    >>> find_previous(1.5, [1, 2])
    (1, 0)
    >>> find_previous(3, [1, 2])
    (2, 1)
    """
    length = len(list_)
    for index, current in enumerate(list_):
        # current is the last element
        if length - 1 == index:
            return current, index

        # current is the first element
        if index == 0:
            if element < current:
                return None, None

        if current <= element < list_[index+1]:
            return current, index
    return None, None


def parse_lyric_text(content: str) -> Dict[int, str]:
    """
    Reference: https://github.com/osdlyrics/osdlyrics/blob/master/python/lrc.py

    >>> parse_lyric_text("[00:00.00] 作曲 : 周杰伦\\n[00:01.00] 作词 : 周杰伦\\n")
    OrderedDict([(0, ' 作曲 : 周杰伦'), (1000, ' 作词 : 周杰伦')])
    """
    ms_sentence_map = OrderedDict()
    sentence_pattern = re.compile(r'\[(\d+(:\d+){0,2}(\.\d+)?)\]')
    lines = content.splitlines()
    for line in lines:
        m = sentence_pattern.search(line, 0)
        if m:
            time_str = m.group(1)
            mileseconds = 0
            unit = 1000
            t_seq = time_str.split(':')
            t_seq.reverse()
            for num in t_seq:
                mileseconds += int(float(num) * unit)
                unit *= 60
            sentence = line[m.end():]
            ms_sentence_map[mileseconds] = sentence
    return ms_sentence_map


Line = namedtuple('Line', ['origin', 'trans', 'has_trans'])


class Lyric:
    def __init__(self, pos_s_map: OrderedDict):
        self._pos_s_map = pos_s_map
        self._pos_list = list(self._pos_s_map.keys())
        self._pos = 0
        self._index: Optional[int] = None
        self._current_s = ''

    @property
    def lines(self):
        return list(self._pos_s_map.values())

    @classmethod
    def from_content(cls, content):
        return cls(parse_lyric_text(content))

    @property
    def current_index(self) -> Optional[int]:
        return self._index

    @property
    def current_s(self):
        return self._current_s

    def update_position(self, pos):
        pos, index = find_previous(pos*1000 + 300, self._pos_list)
        if pos is not None and pos != self._pos:
            self._current_s = self._pos_s_map[pos]
            self._pos = pos
            self._index = index
            return self._current_s, True
        return self._current_s, False


class LiveLyric:
    """live lyric

    LiveLyric listens to song changed signal and position changed signal
    and emit sentence changed signal. It also has a ``current_sentence`` property.

    Usage::

        live_lyric = LiveLyric()
        player.song_changed.connect(live_lyric.on_song_changed)
        player.position_change.connect(live_lyric.on_position_changed)
    """
    def __init__(self, app: App):
        """

        :type app: feeluown.app.App

        .. versionadded:: 3.8.11
            The current_line property.
            The line_changed signal.

        .. versiondeprecated:: 3.8.11
            The current_sentence property.
            The sentence_changed signal.
        """
        self._app = app

        self._lyric: Optional[Lyric] = None
        self._trans_lyric: Optional[Lyric] = None
        self.lyrics_changed = Signal()  # (lyric, trans_lyric, ...)

        self._current_sentence = ''
        self.sentence_changed = Signal()

        self._current_line: Line = Line('', '', False)
        self.line_changed = Signal()

    @property
    def current_lyrics(self):
        # Note that more lyric may be return in the future, for example, KTV lyric.
        # Maybe use a namedtuple like Line in the future.
        return (self._lyric, self._trans_lyric, )

    @property
    def current_sentence(self):
        if self._lyric is None:
            return ''
        return self._lyric.current_s

    @current_sentence.setter
    def current_sentence(self, value):
        self._current_sentence = value
        self.sentence_changed.emit(value)

    @property
    def current_line(self) -> Line:
        if self._lyric is None:
            return Line('', '', False)
        return self._current_line

    @current_line.setter
    def current_line(self, line):
        self._current_line = line
        self.line_changed.emit(line)

    def on_position_changed(self, position):
        if not self._lyric:
            return
        sentence, changed = self._lyric.update_position(position)
        if changed is True:
            has_trans = self._trans_lyric is not None
            if has_trans:
                trans_sentence, _ = self._trans_lyric.update_position(position)
            else:
                trans_sentence = ''
            line = Line(sentence, trans_sentence, has_trans)
            self.current_sentence = sentence
            self.current_line = line

    def on_song_changed(self, song):
        if song is None:
            self.set_lyric(None)
            return

        def cb(future):
            try:
                lyric = future.result()
            except NotSupported:
                lyric = None
            except:  # noqa
                logger.exception('get lyric failed')
                lyric = None
            self.set_lyric(lyric)

        future = aio.run_fn(self._app.library.song_get_lyric, song)
        future.add_done_callback(cb)

    def set_lyric(self, model: LyricModel):
        if model is None:
            self._lyric = self._trans_lyric = None
        elif model.content:
            self._lyric = Lyric.from_content(model.content)
            self._trans_lyric = Lyric.from_content(model.trans_content) \
                if model.trans_content else None
        self.lyrics_changed.emit(self._lyric, self._trans_lyric)
