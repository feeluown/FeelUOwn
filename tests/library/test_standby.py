import random

from feeluown.library.standby import (
    get_standby_score,
    STANDBY_DEFAULT_MIN_SCORE,
    STANDBY_FULL_SCORE,
)
from feeluown.library import BriefSongModel


def test_get_standby_origin_similarity_1():
    origin = BriefSongModel(
        source='',
        identifier='',
        title='x',
        artists_name='y',
    )
    standby1 = BriefSongModel(
        source='',
        identifier='',
        title='z',
        artists_name='y',
    )
    # Should not match
    assert get_standby_score(origin, standby1) < STANDBY_DEFAULT_MIN_SCORE
    standby2 = BriefSongModel(
        source='',
        identifier='',
        title='x',
        artists_name='y',
    )
    # Should match
    assert get_standby_score(origin, standby2) >= STANDBY_DEFAULT_MIN_SCORE


def test_get_standby_origin_similarity_2():
    """A test to check if our score fn works well
    """
    score_fn = get_standby_score

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
    assert score_fn(song, candidates[0]) > \
        score_fn(song, candidates[1])

    # 字符串上一模一样，理应返回满分
    song = create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')
    candidates = [create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')]
    assert score_fn(song, candidates[0]) == STANDBY_FULL_SCORE

    # 根据人工判断，分数应该有 9 分，期望目标算法最起码不能忽略这首歌曲
    song = create_song('很爱很爱你 (Live)', '刘若英',
                       '脱掉高跟鞋 世界巡回演唱会', '05:55')
    candidates = [
        create_song('很爱很爱你', '刘若英', '脱掉高跟鞋世界巡回演唱会', '05:24')
    ]
    assert score_fn(song, candidates[0]) >= STANDBY_DEFAULT_MIN_SCORE
