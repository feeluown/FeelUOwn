import pytest

from feeluown.media import Media


@pytest.fixture
def media():
    return Media('zzz://xxx.yyy',
                 http_headers={'referer': 'http://xxx.yyy'})


def test_media_copy(media):
    media2 = Media(media)
    assert media2.http_headers == media.http_headers
    assert media2.http_proxy == media.http_proxy
    assert media2.decryption_key == media.decryption_key


def test_media_http_headers(media):
    assert 'referer' in media.http_headers


def test_media_decryption_key_default_is_none():
    media = Media('zzz://xxx.yyy')

    assert media.decryption_key is None


def test_media_decryption_key(media):
    media.decryption_key = '0123456789abcdef'
    media2 = Media(media)

    assert media2.decryption_key == '0123456789abcdef'
