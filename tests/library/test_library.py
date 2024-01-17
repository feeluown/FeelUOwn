import random

import pytest

from feeluown.library import (
    ModelType, BriefAlbumModel, BriefSongModel, Provider, Media,
    SimpleSearchResult, Quality
)


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


def test_library_model_get(library, ekaf_provider, ekaf_album0):
    album = library.model_get(ekaf_provider.identifier,
                              ModelType.album,
                              ekaf_album0.identifier)
    assert album.identifier == ekaf_album0.identifier


def test_library_model_upgrade(library, ekaf_provider, ekaf_album0):
    album = BriefAlbumModel(identifier=ekaf_album0.identifier,
                            source=ekaf_provider.identifier)
    album = library._model_upgrade(album)
    assert album.name == ekaf_album0.name


def test_prepare_mv_media(library, ekaf_brief_song0):
    media = library.song_prepare_mv_media(ekaf_brief_song0, '<<<')
    assert media.url != ''  # media url is valid(not empty)


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v2(library):

    class GoodProvider(Provider):
        @property
        def identifier(self):
            return 'good'

        @property
        def name(self):
            return 'good'

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media('good.mp3')

        def search(self, *_, **__):
            return SimpleSearchResult(
                q='',
                songs=[BriefSongModel(identifier='1', source=self.identifier)]
            )

    library.register(GoodProvider())
    song = BriefSongModel(identifier='1', title='try-to-find-standby', source='xxx')
    song_media_list = await library.a_list_song_standby_v2(song)
    assert song_media_list
    assert song_media_list[0][1].url == 'good.mp3'
