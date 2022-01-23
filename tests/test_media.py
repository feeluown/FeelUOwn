import pytest

from feeluown.media import Media


@pytest.fixture
def media():
    return Media('zzz://xxx.yyy',
                 http_headers={'referer': 'http://xxx.yyy'})


def test_media_copy(media):
    media2 = Media(media)
    assert media2.http_headers == media.http_headers


def test_media_http_headers(media):
    assert 'referer' in media.http_headers
