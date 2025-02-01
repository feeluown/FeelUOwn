import json
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from feeluown.config import Config

if TYPE_CHECKING:
    from feeluown.library import BriefSongModel


STANDBY_MATCH_PROMPT = '''\
你是一个音乐播放器助手。你根据“匹配度”帮助用户对搜索候选项进行排序。\
判断匹配度的时候，简体和繁体、英文和中文这些因素都可以忽略，你可以智能转换，然后看是否匹配。\
你要重点考虑原唱这个因素,类似“重制、翻唱、非原创”的歌曲，排序都应该靠后。\
排序完之后，你需要用类似下面的格式来返回，每行一个 JSON，你返回的内容不能包含其它内容

    {"song_id": "xxx", "score": 100, "reason": ""}
    {"song_id": "yyy", "score": 95, "reason": ""}
'''


def song_as_jsonline(song: 'BriefSongModel'):
    js = {
        'title': song.title,
        'artists_name': song.artists_name,
    }
    if song.album_name:
        js['album_name'] = song.album_name,
    if song.duration_ms:
        js['duration_ms'] = song.duration_ms,
    return json.dumps(js)


def standby_list_as_jsonlines(songs: 'BriefSongModel'):
    lines = []
    for song in songs:
        js = {
            'song_id': f'{song.source}___{song.identifier}',
            'title': song.title,
            'artists_name': song.artists_name,
            'album_name': song.album_name,
            'duration_ms': song.duration_ms,
        }
        lines.append(json.dumps(js))
    return '\n'.join(lines)


class AI:
    def __init__(self, base_url, api_key, model):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def get_async_client(self):
        return AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
