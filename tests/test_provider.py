from feeluown.media import Quality
from feeluown.library import ProviderV2


def test_library_song_select_media(mocker, song):
    valid_q_list = [Quality.Audio.sq]
    mocker.patch.object(ProviderV2, 'song_list_quality',
                        return_value=valid_q_list)
    mocker.patch.object(ProviderV2, 'song_get_media')
    provider = ProviderV2()
    _, q = provider.song_select_media(song, None)
    assert q == valid_q_list[0]
