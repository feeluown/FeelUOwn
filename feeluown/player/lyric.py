import re
import logging
from typing import Dict, List

from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from feeluown.utils.utils import find_previous

logger = logging.getLogger(__name__)


def parse_lyric_text(content: str) -> Dict[int, str]:
    """
    Reference: https://github.com/osdlyrics/osdlyrics/blob/master/python/lrc.py

    >>> parse_lyric_text("[00:00.00] 作曲 : 周杰伦\\n[00:01.00] 作词 : 周杰伦\\n")
    {0: ' 作曲 : 周杰伦', 1000: ' 作词 : 周杰伦'}
    """
    ms_sentence_map = dict()
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


class LiveLyric(object):
    """live lyric

    LiveLyric listens to song changed signal and position changed signal
    and emit sentence changed signal. It also has a ``current_sentence`` property.

    Usage::

        live_lyric = LiveLyric()
        player.song_changed.connect(live_lyric.on_song_changed)
        player.position_change.connect(live_lyric.on_position_changed)
    """
    def __init__(self, app):
        """

        :type app: feeluown.app.App
        """
        self._app = app
        self.sentence_changed = Signal(str)

        self._lyric = None
        self._pos_s_map: Dict[int, str] = {}  # position sentence map
        self._pos_list: List[int] = []  # position list
        self._pos = None

        self._current_sentence = ''

    @property
    def current_sentence(self):
        """get current lyric sentence"""
        return self._current_sentence

    @current_sentence.setter
    def current_sentence(self, value):
        self._current_sentence = value
        self.sentence_changed.emit(value)

    # TODO: performance optimization?
    def on_position_changed(self, position):
        """bind position changed signal with this"""
        if position is None or not self._lyric:
            return

        pos = find_previous(position*1000 + 300, self._pos_list)
        if pos is not None and pos != self._pos:
            self.current_sentence = self._pos_s_map[pos]
            self._pos = pos

    def on_song_changed(self, song):
        """bind song changed signal with this"""
        if song is None:
            self._set_lyric(None)
            return

        def cb(future):
            try:
                lyric = future.result()
            except:  # noqa
                logger.exception('get lyric failed')
                lyric = None
            self._set_lyric(lyric)

        future = aio.run_fn(self._app.library.song_get_lyric, song)
        future.add_done_callback(cb)

    def _set_lyric(self, lyric):
        if lyric is None or lyric.content is None:
            self._lyric = None
            self._pos_s_map = {}
        else:
            self._lyric = lyric.content
            self._pos_s_map = parse_lyric_text(self._lyric)
            self._pos_list = sorted(list(self._pos_s_map.keys()))
            self._pos = None
            self.current_sentence = ''
