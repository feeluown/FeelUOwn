from unittest.mock import MagicMock
import pytest

from feeluown.library import (
    ProviderV2, ModelType, ProviderFlags as PF,
    AlbumModel, ArtistModel, BriefVideoModel, BriefSongModel,
    Library, SongModel, BriefAlbumModel, BriefArtistModel, SimpleSearchResult
)
from feeluown.media import Quality, Media, MediaType
from feeluown.utils.reader import create_reader


FakeSource = 'fake'  # v1 provider
EkafSource = 'ekaf'  # v2 provider


class FakeProvider(ProviderV2):
    class meta:
        identifier = 'fake'
        name = 'FAKE'

    @property
    def identifier(self):
        return 'fake'

    @property
    def name(self):
        return 'FAKE'

    def search(self, keyword, **kwargs):
        return SimpleSearchResult(q=keyword, songs=[_song1, _song2, _song3])


class EkafProvider(ProviderV2):
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

    def song_get(self, identifier):
        if identifier == _ekaf_song0.identifier:
            return _ekaf_song0

    def song_list_quality(self, song):
        return []

    def song_get_media(self, song, quality):
        return []

    def song_get_mv(self, song):
        if song.identifier == _ekaf_brief_song0.identifier:
            return _ekaf_brief_mv0

    def album_get(self, identifier):
        if identifier == _ekaf_album0.identifier:
            return _ekaf_album0

    def artist_get(self, identifier):
        if identifier == _ekaf_artist0.identifier:
            return _ekaf_artist0

    def artist_create_songs_rd(self, _):
        return create_reader([])

    def video_list_quality(self, video):
        if video.identifier == _ekaf_brief_mv0.identifier:
            return [Quality.Video.hd]

    def video_get_media(self, video, quality):
        if video.identifier == _ekaf_brief_mv0.identifier \
           and quality is Quality.Video.hd:
            return Media('http://ekaf.org/mv0.mp4',
                         type_=MediaType.video,)
        return None


_fake_provider = FakeProvider()
_song1 = SongModel(source=FakeSource,
                   identifier='1', title='1', album=None,
                   artists=[], duration=0)
_song2 = SongModel(source=FakeSource,
                   identifier='2', title='2', album=None,
                   artists=[], duration=0)
_song3 = SongModel(source=FakeSource,
                   identifier='3', title='3', album=None,
                   artists=[], duration=0)


_ekaf_brief_song0 = BriefSongModel(source=EkafSource,
                                   identifier='0')
_ekaf_brief_album0 = BriefAlbumModel(source=EkafSource,
                                     identifier='0')
_ekaf_brief_artist0 = BriefArtistModel(source=EkafSource,
                                       identifier='0')
_ekaf_album0 = AlbumModel(source=EkafSource,
                          identifier='0', name='0', cover='',
                          description='', songs=[], artists=[])
_ekaf_artist0 = ArtistModel(source=EkafSource,
                            identifier='0', name='0', pic_url='',
                            description='', hot_songs=[], aliases=[])
_ekaf_brief_mv0 = BriefVideoModel(source=EkafSource,
                                  identifier='0', title='')
_ekaf_song0 = SongModel(source=EkafSource,
                        identifier='0', title='0', album=_ekaf_brief_album0,
                        artists=[_ekaf_brief_artist0], duration=0)


@pytest.fixture
def ekaf_brief_song0():
    return _ekaf_brief_song0


@pytest.fixture
def ekaf_song0():
    return _ekaf_song0


@pytest.fixture
def ekaf_album0():
    return _ekaf_album0


@pytest.fixture
def ekaf_artist0():
    return _ekaf_artist0


@pytest.fixture
def artist():
    return BriefArtistModel(identifier=0, source='fake', name='mary')


@pytest.fixture
def album(artist):
    return AlbumModel(
        identifier=0,
        source='fake',
        name='blue and green',
        artists=[],
        songs=[],
        cover='',
        description='',
    )


@pytest.fixture
def song(artist, album):
    return SongModel(
        identifier='0',
        source=FakeSource,
        title='hello world',
        artists=[artist],
        album=album,
        duration=600000,
        )
    # url='http://xxx.com/xxx.mp3'


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
