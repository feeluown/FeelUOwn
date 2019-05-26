from unittest.mock import MagicMock

import pytest

from fuocore.library import Library
from fuocore import models
from fuocore.provider import AbstractProvider


class FakeProvider(AbstractProvider):

    @property
    def identifier(self):
        return 'fake'

    @property
    def name(self):
        return 'Fake'

    def search(self, keyword, **kwargs):
        return FakeSearchModel(q=keyword, songs=[_song1, _song2, _song3])


fake_provider = FakeProvider()


class FakeSongModel(models.SongModel):
    class Meta:
        provider = fake_provider


class FakeArtistModel(models.ArtistModel):
    class Meta:
        provider = fake_provider


class FakeAlbumModel(models.AlbumModel):
    class Meta:
        provider = fake_provider


class FakeSearchModel(models.SearchModel):
    class Meta:
        provider = fake_provider


_song1 = FakeSongModel(identifier=1, url='1.mp3')
_song2 = FakeSongModel(identifier=2, url='2.mp3')
_song3 = FakeSongModel(identifier=3)


@pytest.fixture
def artist():
    return FakeArtistModel(identifier=0, name='mary')


@pytest.fixture
def album():
    return FakeAlbumModel(identifier=0, name='blue and green')


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
def song1(): return _song1


@pytest.fixture
def song2(): return _song2


@pytest.fixture
def song3(): return _song3


@pytest.fixture
def provider():
    return fake_provider


@pytest.fixture
def library(provider):
    library = Library()
    library.register(provider)
    return library


@pytest.fixture
def app_mock():
    return MagicMock()
