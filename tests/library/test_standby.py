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
        return BriefSongModel(
            identifier=random.randint(0, 1000),
            source='x',
            title=title,
            artists_name=artists_name,
            album_name=album_name,
            duration_ms=duration_ms
        )

    # A real case: the song comes from platform A, and
    # the candidate songs are from platform B’s search results.
    # By human judgment, the first result meets expectations.
    #
    # Here’s a feature: the title of the first result has a suffix,
    # but this suffix is redundant and has no impact.
    # This phenomenon is very common on the Kuwo platform.
    song = create_song('暖暖', '梁静茹', '亲亲', '04:03')
    candidates = [
        create_song(*x) for x in [
            ('暖暖-《周末父母》电视剧片头曲', '梁静茹', '亲亲', '04:06'),
            ('暖暖', '梁静茹', '“青春19潮我看”湖南卫视2018-2019跨年演唱会', '01:57'),
            ('暖暖 (2011音乐万万岁现场)', '梁静茹', '', '03:50'),
            ('暖暖 (2015江苏卫跨年演唱会)', '梁静茹', '', '02:05'),
            ('暖暖 (纯音乐)', '梁静茹', '', '03:20'),
            ('暖暖 (DJ版)', '梁静茹', '', '03:16'),
            ('暖暖(Cover 梁静茹)', '釉哥哥&光光', '暖暖-梁静茹', '04:06'),
        ]
    ]
    assert score_fn(song, candidates[0]) > \
        score_fn(song, candidates[1])

    # The strings are exactly the same, so it should return a perfect score
    song = create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')
    candidates = [create_song('我很想爱他', 'Twins', '八十块环游世界', '04:27')]
    assert score_fn(song, candidates[0]) == STANDBY_FULL_SCORE

    # According to manual judgment, the score should be 9 points,
    # and we expect the target algorithm to at least not ignore this song
    song = create_song('很爱很爱你 (Live)', '刘若英', '脱掉高跟鞋 世界巡回演唱会', '05:55')
    candidates = [create_song('很爱很爱你', '刘若英', '脱掉高跟鞋世界巡回演唱会', '05:24')]
    assert score_fn(song, candidates[0]) >= STANDBY_DEFAULT_MIN_SCORE
