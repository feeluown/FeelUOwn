#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from fuocore.library import Library

from fuocore.xiami import provider as xp
from fuocore.netease import provider as np
from fuocore.qqmusic import provider as lp

logging.basicConfig()
logger = logging.getLogger('fuocore')
logger.setLevel(logging.DEBUG)

lib = Library()
lib.register(xp)
lib.register(np)
lib.register(lp)


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
