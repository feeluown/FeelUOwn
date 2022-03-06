import random

import pytest

from feeluown.library import Library, ModelType, BriefAlbumModel
from feeluown.library.provider import dummy_provider
from feeluown.models import SearchModel


def test_library_search(library):
    result = list(library.search('xxx'))[0]
    assert len(result.songs) >= 3
    assert result.songs[0].identifier == 1


@pytest.mark.asyncio
async def test_library_a_search(library):
    result = [x async for x in library.a_search('xxx')][0]
    assert result.q == 'xxx'


def test_score_fn():
    """A test to check if our score fn works well
    """
    from feeluown.library.models import BriefSongModel
    from feeluown.library.library import default_score_fn, FULL_SCORE, MIN_SCORE

    def create_song(title, artists_name, album_name, duration_ms):
        return BriefSongModel(identifier=random.randint(0, 1000),
                              source='x',
                              title=title,
                              artists_name=artists_name,
                              album_name=album_name,
                              duration_ms=duration_ms)

    # 一个真实案例：歌曲来自 a 平台，候选歌曲来自 b 平台的搜索结果。
    # 人为判断，第一个结果是符合预期的。
    #
    # 这里有一个特点：第一个结果的标题有个后缀，但这个后缀是多余且无影响的信息。
    # 这个现象在 kuwo 平台非常常见。
    song = create_song('暖暖', '梁静茹', '亲亲', '04:03')
    candidates = [create_song(*x) for x in [
        ('暖暖-《周末父母》电视剧片头曲', '梁静茹', '亲亲', '04:06'),
        ('暖暖', '梁静茹', '“青春19潮我看”湖南卫视2018-2019跨年演唱会', '01:57'),
        ('暖暖 (2011音乐万万岁现场)', '梁静茹', '', '03:50'),
        ('暖暖 (2015江苏卫跨年演唱会)', '梁静茹', '', '02:05'),
        ('暖暖 (纯音乐)', '梁静茹', '', '03:20'),
        ('暖暖 (DJ版)', '梁静茹', '', '03:16'),
        ('暖暖(Cover 梁静茹)', '釉哥哥&光光', '暖暖-梁静茹', '04:06'),
    ]]
    assert default_score_fn(song, candidates[0]) > \
        default_score_fn(song, candidates[1])

    # 字符串上一模一样，理应返回满分
    song = create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')
    candidates = [create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')]
    assert default_score_fn(song, candidates[0]) == FULL_SCORE

    # 根据人工判断，分数应该有 9 分，期望目标算法最起码不能忽略这首歌曲
    song = create_song('很爱很爱你 (Live)', '刘若英',
                       '脱掉高跟鞋 世界巡回演唱会', '05:55')
    candidates = [
        create_song('很爱很爱你', '刘若英', '脱掉高跟鞋世界巡回演唱会', '05:24')
    ]
    assert default_score_fn(song, candidates[0]) >= MIN_SCORE


def test_library_list_songs_standby(library, song):
    songs = library.list_song_standby(song)

    # all songs share the same provider,
    # so there will be no standby song
    assert len(songs) == 0

    song.source = 'dummy-1'
    songs = library.list_song_standby(song)
    assert len(songs) == 1

    songs = library.list_song_standby(song, onlyone=False)
    assert len(songs) == 2


@pytest.mark.asyncio
async def test_library_a_list_songs_standby(library, song):
    songs = await library.a_list_song_standby(song)
    assert len(songs) <= 1

    song.source = 'dummy-1'
    songs = await library.a_list_song_standby(song)
    assert len(songs) == 1


@pytest.mark.asyncio
async def test_library_a_list_songs_standby_with_specified_providers(song):
    library = Library(providers_standby=['xxx'])
    song.source = 'dummy-1'
    songs = await library.a_list_song_standby(song)
    assert len(songs) == 0


@pytest.mark.asyncio
async def test_library_a_list_songs_standby_v2(library, provider,
                                               song, song1, song_standby, mocker):
    mock_search = mocker.patch.object(provider, 'search')
    mock_search.return_value = SearchModel(q='xx', songs=[song1, song_standby])

    song_media_list = await library.a_list_song_standby_v2(song)
    for standby, media in song_media_list:
        if standby is song_standby:
            assert media.url == 'standby.mp3'
            break
    else:
        assert False, 'song_standby should be a stanby option'


def test_library_register_should_emit_signal(library, mocker):
    mock_emit = mocker.patch('feeluown.utils.dispatch.Signal.emit')
    library.register(dummy_provider)
    mock_emit.assert_called_once_with(dummy_provider)


def test_library_model_get(xlibrary, eee_provider):
    album = xlibrary.model_get(eee_provider.identifier, ModelType.album, '0')
    assert album.identifier == '0'


def test_library_model_upgrade(xlibrary, eee_provider):
    album = BriefAlbumModel(identifier='0',
                            source=eee_provider.identifier,)
    album = xlibrary._model_upgrade(album)
    assert album.name == '0'
