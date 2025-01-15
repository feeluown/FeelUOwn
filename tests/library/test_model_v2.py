import pytest
import pydantic

from feeluown.library import SongModel, BriefAlbumModel, BriefArtistModel, BriefSongModel


def test_create_song_model_basic():
    identifier = '1'
    brief_album = BriefAlbumModel(identifier='1', source='x',
                                  name='Film', artists_name='Audrey')
    brief_artist = BriefArtistModel(identifier='1', source='x', name='Audrey')
    # song should be created
    song = SongModel(identifier=identifier, source='x', title='Moon', album=brief_album,
                     artists=[brief_artist], duration=240000)
    # check song's attribute value
    assert song.artists_name == 'Audrey'

    # song model cache get/set
    song.cache_set('count', 1)
    assert song.cache_get('count') == (1, True)


def test_create_model_with_extra_field():
    with pytest.raises(pydantic.ValidationError):
        BriefSongModel(identifier=1, source='x', unk=0)


def test_song_model_is_hashable():
    """
    Song model must be hashable.
    """
    song = BriefSongModel(identifier=1, source='x')
    hash(song)
