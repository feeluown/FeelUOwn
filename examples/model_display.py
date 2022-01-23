#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from fuo_netease.models import NSongModel

logging.basicConfig()
logger = logging.getLogger('feeluown')
logger.setLevel(logging.DEBUG)


def test_model_display():
    song = NSongModel.create_by_display(
            identifier=254548,
            title='成全',
            artists_name='刘若英')
    assert song.album_name_display == ''
    assert song.title_display == '成全'
    print(song.url, song.title)
    assert song.album_name_display != ''


def main():
    test_model_display()


if __name__ == '__main__':
    main()
