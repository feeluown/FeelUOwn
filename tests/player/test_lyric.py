import asyncio
import pytest

from feeluown.player import LiveLyric, parse_lyric_text
from feeluown.library import LyricModel


lyric = """[by:魏积分]
[00:38.01]大都会に　僕はもう一人で
[00:47.13]投げ捨てられた　空カンのようだ
[00:54.29]互いのすべてを　知りつくすまでが
[01:03.06]愛ならば　いっそ　永久（とわ）に眠ろうか
[01:12.10]世界が終るまでは
[01:17.10]離れる事もない
[01:22.03]そう願っていた
[01:26.97]幾千の夜と
[01:30.29]戻らない時だけが
[01:35.08]何故輝いては
[01:41.36]やつれ切った　心までも　壊す
[01:49.39]はかなき想い
[01:54.60]このTragedy Night
[02:01.85]
[02:05.00]そして人は　形（こたえ）を求めて
[02:15.13]かけがえのない　何かを失う
[02:22.20]欲望だらけの　街じゃ　夜空の
[02:31.19]星屑も　僕らを　灯せない
[02:39.08]世界が终る前に
[02:45.39]聞かせておくれよ
[02:50.38]満開の花が
[02:54.81]似合いのCatastrophe
[02:58.65]誰もが望みながら　永遠を信じない
[03:08.71]なのに　きっと　明日を夢見てる
[03:17.21]はかなき日々と
[03:21.21]このTragedy Night
[03:29.21]
[03:48.06]世界が終るまでは　離れる事もない
[03:58.64]そう願っていた　幾千の夜と
[04:07.47]戻らない時だけが　何故輝いては
[04:16.12]やつれ切った　心までも　壊す
[04:25.09]はかなき想い
[04:31.41]このTragedy Night
[04:36.31]このTragedy Night
"""

SomeoneLikeYou = """
[00:00.000] 作词 : Adele Adkins/Dan Wilson
[00:01.000] 作曲 : Adele Adkins/Dan Wilson
[00:12.737]I heard
[00:16.478]That you are settled down
[00:21.789]That you found a girl
[00:23.557]And you are married now
[00:28.728]I heard
[00:31.590]That your dreams came true
"""

SomeoneLikeYouTrans = """
[by:baekhyun_josae]
[00:12.737]听说
[00:16.478]你心有所属
[00:21.789]你遇到了她
[00:23.557]已经步入婚姻殿堂
[00:28.728]听说
[00:31.590]你美梦成真
"""


class FakeLyric(object):
    def __init__(self):
        self.content = lyric


@pytest.mark.asyncio
async def test_no_song_changed(app_mock):
    app_mock.library.song_get_lyric.return_value = FakeLyric()
    live_lyric = LiveLyric(app_mock)
    song = object()
    live_lyric.on_song_changed(song)
    await asyncio.sleep(0.1)
    live_lyric.on_position_changed(60)
    assert live_lyric.current_sentence == '互いのすべてを　知りつくすまでが'


def test_live_lyric_with_trans(app_mock):
    model = LyricModel(identifier=1,
                       source='local',
                       content=SomeoneLikeYou,
                       trans_content=SomeoneLikeYouTrans)
    live_lyric = LiveLyric(app_mock)
    live_lyric.set_lyric(model)

    live_lyric.on_position_changed(3)
    assert live_lyric.current_sentence == ' 作曲 : Adele Adkins/Dan Wilson'
    current_line = live_lyric.current_line
    assert current_line[0] == live_lyric.current_sentence
    assert current_line[2]
    assert current_line[1] == ''

    live_lyric.on_position_changed(29)
    assert live_lyric.current_sentence == 'I heard'
    current_line = live_lyric.current_line
    assert current_line[0] == live_lyric.current_sentence
    assert current_line[1] == '听说'
    assert current_line[2]

    live_lyric.set_lyric(None)
    assert live_lyric.current_sentence == ''
    assert live_lyric.current_line[0] == ''
    assert live_lyric.current_line[2] is False


def test_parse_ill_formed_lyric():
    result = parse_lyric_text('''
[00:00.00] 作词 : シャノン
[00:00.05] 作曲 : シャノン
[00:00:10]僕らの最後は死別にしよう
[00:05:64]嫌いになりそうな日差しの中
''')
    assert result[50] == ' 作曲 : シャノン'
    assert result[100] == '僕らの最後は死別にしよう'
