from feeluown.media import Quality
from feeluown.library import ProviderV2


def test_library_song_select_media(mocker):
    provider = ProviderV2()
    valid_q_list = [Quality.Audio.sq]
    mocker.patch.object(provider, 'song_list_quality',
                        return_value=valid_q_list)
    mocker.patch.object(provider, 'song_get_media')
    song = object()
    _, q = provider.song_select_media(song, None)
    assert q == valid_q_list[0]
