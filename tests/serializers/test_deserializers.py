import pytest

from feeluown.library import SongModel
from feeluown.serializers import serialize, deserialize


@pytest.fixture
def asong_data():
    return {
        'album': {'artists_name': '',
                  'identifier': '84557',
                  'name': '腔·调',
                  'source': 'xx'},
        'album_name': '腔·调',
        'artists': [
            {'identifier': '4445', 'name': '毛阿敏', 'source': 'xx'}
        ],
        'artists_name': '毛阿敏',
        'children': [],
        'date': '',
        'disc': '1/1',
        'duration': 181000,
        'duration_ms': '03:01',
        'genre': '',
        'identifier': '106329564',
        'media_flags': 128,
        'pic_url': '',
        'title': '相思',
        'track': '1/1',
        'source': 'xx'
    }


@pytest.fixture
def asong(asong_data):
    return SongModel.model_validate(asong_data)


def test_deserializer_basic_types():
    assert deserialize('python', 1) == 1
    assert deserialize('python', 'h') == 'h'
    assert deserialize('python', 1.1) == 1.1
    assert deserialize('python', None) is None


def test_deserialize_model_from_valid_json(asong):
    data = serialize('python', asong)
    song2 = deserialize('python', data)
    assert song2.artists[0] == asong.artists[0]


def test_deserialize_models(asong):
    songs = [asong, asong]
    data = serialize('python', songs)
    songs2 = deserialize('python', data)
    assert songs == songs2
