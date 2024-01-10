from unittest import mock

import pytest

from feeluown.library import reverse
from feeluown.library import ModelNotFound
from feeluown.gui.helpers import fetch_cover_wrapper


async def img_mgr_get_return_x():
    return b'x'


@pytest.mark.asyncio
async def test_fetch_cover_wrapper(app_mock, library,
                                   ekaf_brief_song0, ekaf_album0, ekaf_song0,
                                   song):
    app_mock.library = library
    app_mock.img_mgr.get_from_cache.return_value = None
    mock_img_mgr_get = app_mock.img_mgr.get
    song_pic_uri = reverse(ekaf_song0, '/pic_url')
    album_cover_uri = reverse(ekaf_album0, '/cover')

    # case 1: when song is a v2 model and it has pic_url, it should directly used.
    url = 'http://xxx.com/cover.jpg'
    ekaf_song0.pic_url = url
    cb = mock.MagicMock()
    mock_img_mgr_get.return_value = img_mgr_get_return_x()
    coro = fetch_cover_wrapper(app_mock)
    await coro(ekaf_brief_song0, cb)
    mock_img_mgr_get.assert_called_once_with(url, song_pic_uri)
    cb.assert_called_once_with(b'x')

    # case 2: song.pic_url is empty and its album has valid cover,
    # the cover should be used.
    ekaf_song0.pic_url = ''
    ekaf_album0.cover = 'http://xxx.com/cover.jpg'
    cb = mock.MagicMock()
    app_mock.img_mgr.get.return_value = img_mgr_get_return_x()
    coro = fetch_cover_wrapper(app_mock)
    await coro(ekaf_brief_song0, cb)
    mock_img_mgr_get.assert_called_with(url, album_cover_uri)
    cb.assert_called_once_with(b'x')

    # case 3: song is a v1 model, and it's album has valid cover.
    app_mock.img_mgr.get.return_value = img_mgr_get_return_x()
    song.album.cover = 'http://xxx.com/cover.jpg'
    cb = mock.MagicMock()
    coro = fetch_cover_wrapper(app_mock)
    await coro(song, cb)
    cb.assert_called_once_with(b'x')

    # case 4: song has no valid album
    song.album.cover = ''
    cb = mock.MagicMock()
    coro = fetch_cover_wrapper(app_mock)
    await coro(song, cb)
    cb.assert_called_once_with(None)

    # case 5: song can not be upgraded
    mock_upgrad_song = mock.MagicMock()
    app_mock.library.song_upgrade = mock_upgrad_song
    mock_upgrad_song.side_effect = ModelNotFound
    cb = mock.MagicMock()
    coro = fetch_cover_wrapper(app_mock)
    await coro(ekaf_brief_song0, cb)
    cb.assert_called_once_with(None)
