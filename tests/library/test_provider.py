from feeluown.media import Quality
from feeluown.library import ModelType


def test_library_song_select_media(mocker, ekaf_provider, song):
    valid_q_list = [Quality.Audio.sq]
    mocker.patch.object(ekaf_provider, 'song_list_quality',
                        return_value=valid_q_list)
    mocker.patch.object(ekaf_provider, 'song_get_media')
    _, q = ekaf_provider.song_select_media(song, None)
    assert q == valid_q_list[0]


def test_use_model_v2(ekaf_provider):
    assert ekaf_provider.use_model_v2(ModelType.album) is True
    assert ekaf_provider.use_model_v2(ModelType.dummy) is False
