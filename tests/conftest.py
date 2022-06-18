from unittest.mock import MagicMock
import pytest

from feeluown import models
from feeluown.library import (
    AbstractProvider, ProviderV2, ModelType, ProviderFlags as PF,
    AlbumModel, ArtistModel,
    Library,
)
from feeluown.utils.reader import create_reader


FakeSource = 'fake'
EkafSource = 'ekaf'


class FakeProvider(AbstractProvider):

    @property
    def identifier(self):
        return 'fake'

    @property
    def name(self):
        return 'FAKE'

    def search(self, keyword, **kwargs):
        return FakeSearchModel(q=keyword, songs=[_song1, _song2, _song3])


class EkafProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = 'ekaf'
        name = 'EKAF'
        flags = {
            ModelType.album: (PF.model_v2 | PF.get),
            ModelType.artist: (PF.model_v2 | PF.get | PF.songs_rd),
        }

    def __init__(self):
        super().__init__()

    @property
    def identifier(self):
        return EkafSource

    @property
    def name(self):
        return 'EKAF'

    def song_list_quality(self, song):
        return []

    def song_get_media(self, song, quality):
        return []

    def album_get(self, identifier):
        if identifier == _ekaf_album0.identifier:
            return _ekaf_album0

    def artist_get(self, identifier):
        if identifier == _ekaf_artist0.identifier:
            return _ekaf_artist0

    def artist_create_songs_rd(self, _):
        return create_reader([])


_fake_provider = FakeProvider()


class FakeSongModel(models.SongModel):
    class Meta:
        provider = _fake_provider


class FakeArtistModel(models.ArtistModel):
    class Meta:
        provider = _fake_provider


class FakeAlbumModel(models.AlbumModel):
    class Meta:
        provider = _fake_provider


class FakeSearchModel(models.SearchModel):
    class Meta:
        provider = _fake_provider


_song1 = FakeSongModel(identifier=1, url='1.mp3')
_song2 = FakeSongModel(identifier=2, url='2.mp3')
_song3 = FakeSongModel(identifier=3)
_ekaf_album0 = AlbumModel(source=EkafSource,
                          identifier='0', name='0', cover='',
                          description='', songs=[], artists=[])
_ekaf_artist0 = ArtistModel(source=EkafSource,
                            identifier='0', name='0', pic_url='',
                            description='', hot_songs=[], aliases=[])


@pytest.fixture
def artist():
    return FakeArtistModel(identifier=0, name='mary')


@pytest.fixture
def album():
    return FakeAlbumModel(identifier=0, name='blue and green')


@pytest.fixture
def ekaf_album0():
    return _ekaf_album0


@pytest.fixture
def ekaf_artist0():
    return _ekaf_artist0


@pytest.fixture
def song(artist, album):
    return FakeSongModel(
        identifier=0,
        title='hello world',
        artists=[artist],
        album=album,
        duration=600000,
        url='http://xxx.com/xxx.mp3')


@pytest.fixture
def song_standby(song):
    return FakeSongModel(
        identifier=100,
        title=song.title,
        artists=song.artists,
        album=song.album,
        duration=song.duration,
        url='standby.mp3'
    )


@pytest.fixture
def song1(): return _song1


@pytest.fixture
def song2(): return _song2


@pytest.fixture
def song3(): return _song3


@pytest.fixture
def provider():
    """provider is a v1 provider"""
    return _fake_provider


@pytest.fixture
def ekaf_provider():
    """ekaf_provider is a v2 provider"""
    return EkafProvider()


@pytest.fixture
def library(provider, ekaf_provider):
    library = Library()
    library.register(provider)
    library.register(ekaf_provider)
    return library


@pytest.fixture
def app_mock():
    return MagicMock()
