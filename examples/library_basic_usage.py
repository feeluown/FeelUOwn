#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
You should install two package from pypi:

1. fuo-netease
2. fuo-xiami
"""

import logging
from feeluown.library import Library

from fuo_xiami import provider as xp
from fuo_netease import provider as np

logging.basicConfig()
logger = logging.getLogger('feeluown')
logger.setLevel(logging.DEBUG)

lib = Library()
lib.register(xp)
lib.register(np)


def test_list_song_standby():
    """
    使用 library.list_song_standby 接口
    """
    result = xp.search('小小恋歌 新垣结衣', limit=2)
    song = result.songs[0]  # 虾米音乐没有这首歌的资源
    assert song.url == ''

    standby_songs = lib.list_song_standby(song)
    for index, ss in enumerate(standby_songs):  # pylint: disable=all
        print(index, ss.source, ss.title, ss.artists_name, ss.url)


def main():
    test_list_song_standby()


if __name__ == '__main__':
    main()
