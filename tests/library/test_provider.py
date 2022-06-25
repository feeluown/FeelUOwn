from feeluown.media import Quality


def test_library_song_select_media(mocker, ekaf_provider, song):
    valid_q_list = [Quality.Audio.sq]
    mocker.patch.object(ekaf_provider, 'song_list_quality',
                        return_value=valid_q_list)
    mocker.patch.object(ekaf_provider, 'song_get_media')
    _, q = ekaf_provider.song_select_media(song, None)
    assert q == valid_q_list[0]
