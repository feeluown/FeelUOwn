import asyncio
import logging
import json
from typing import List, TYPE_CHECKING

from feeluown.ai import a_handle_stream
from feeluown.utils.aio import run_afn, as_completed

if TYPE_CHECKING:
    from feeluown.ai import AI
    from feeluown.library import BriefSongModel

logger = logging.getLogger(__name__)


class AIStandbyMatcher:
    # 调试的使用，可以考虑把 reason 字段也带上。
    #   {"song_id": "xxx", "score": 100, "reason": ""}
    #   {"song_id": "yyy", "score": 95, "reason": ""}
    #
    #   {"song_id": "xxx", "score": 100}
    #   {"song_id": "yyy", "score": 95}
    STANDBY_MATCH_PROMPT = '''\
你是一个音乐播放器助手。你根据“匹配度”帮助用户对搜索候选项进行排序。\
判断匹配度的时候，简体和繁体、英文和中文这些因素都可以忽略，你可以智能转换，然后看是否匹配。\
你要重点考虑原唱这个因素,类似“重制、翻唱、非原创”的歌曲，排序都应该靠后。\
排序完之后，你需要用类似下面的格式来返回，每行一个 JSON，你返回的内容不能包含其它内容

    {"song_id": "xxx", "score": 100}
    {"song_id": "yyy", "score": 95}
'''

    def __init__(self, ai: 'AI', a_prepare_media, min_score, audio_select_policy):
        self.ai = ai
        self._prepare_media = a_prepare_media

        self.min_score = min_score
        self.audio_select_policy = audio_select_policy

        # during runtime
        self.fetch_media_tasks = {}
        self.song_by_source = {}

    async def match(self, song: 'BriefSongModel', standby_list: List['BriefSongModel']):
        sys_msg = {'role': 'system', 'content': self.STANDBY_MATCH_PROMPT}
        user_msg = {
            'role': 'user',
            'content': (f'我搜索了 `{self.song_as_jsonline(song)}`\n'
                        '应用返回的候选项如下：\n'
                        f'{self.standby_list_as_jsonlines(standby_list)}')
        }
        logger.info(f"Try to find {song} standby, user msg: {user_msg['content']}")
        client = self.ai.get_async_client()
        try:
            stream = await client.chat.completions.create(
                model=self.ai.model,
                messages=[sys_msg, user_msg],
                stream=True,
            )
        except:  # noqa
            logger.exception('AI request failed')
            return []

        rr, rw, wtask = await a_handle_stream(stream)
        source_media_pair = None
        while True:
            try:
                lineb = await rr.readline()
            except:  # noqa
                logger.exception('readline failed')
                break
            if not lineb:
                break

            source_media_pair = await self.try_get_source_media_pair()
            if source_media_pair:
                logger.info(f'Standby from ${source_media_pair[0]} is available')
                await stream.close()
                break

            line = lineb.decode('utf-8')
            logger.debug(f"{song} standby: {line}")
            try:
                song_json = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(f'invalid json line: {line}')
                continue
            if song_json['score'] < self.min_score:
                continue
            try:
                source, identifier = song_json['song_id'].split('___')
            except ValueError:
                logger.error(f'AI returns a invalid response: {song_json}')
                break
            if source in self.song_by_source:  # Only use the first song for each source.
                continue
            for standby in standby_list:
                if standby.source == source and standby.identifier == identifier:
                    self.song_by_source[source] = standby
                    task = run_afn(
                        self._prepare_media, standby, self.audio_select_policy)
                    self.fetch_media_tasks[source] = task

        try:
            await wtask
        except:  # noqa
            if not source_media_pair:
                logger.exception('Stream consumer error')
        rw.close()
        await rw.wait_closed()

        if not source_media_pair:
            source_media_pair = await self.wait_and_get_source_media_pair()
        if source_media_pair:
            self.cancel_fetch_media_tasks()
            standby = self.song_by_source[source_media_pair[0]]
            media = source_media_pair[1]
            logger.debug(f'Standby matched for {song}')
            return [(standby, media)]
        logger.debug(f'No standby matched for {song}')
        return []

    async def try_get_source_media_pair(self):
        source_media_pair_ = None
        for source, task in self.fetch_media_tasks.items():
            if task.done():
                _media = task.result()
                if _media is not None:
                    source_media_pair_ = (source, _media)
                    break
        return source_media_pair_

    async def wait_and_get_source_media_pair(self):
        fs = self.fetch_media_tasks.values()
        # TODO: add timeout
        for future in as_completed(fs, timeout=None):
            try:
                media = await future
            except:  # noqa
                logger.exception('fetch media task failed')
                continue
            else:
                # When a provider does not implement search method, it returns None.
                source = None
                for source, task in self.fetch_media_tasks.items():
                    if future == task:
                        source = source
                        break
                if media is not None:
                    return (source, media)
                else:
                    logger.debug('No media available in source:${source}')
        return None

    def cancel_fetch_media_tasks(self):
        for source, task in self.fetch_media_tasks.items():
            if not task.done():
                task.cancel()

    @classmethod
    def song_as_jsonline(cls, song: 'BriefSongModel'):
        js = {
            'title': song.title,
            'artists_name': song.artists_name,
        }
        if song.album_name:
            js['album_name'] = song.album_name,
        if song.duration_ms:
            js['duration_ms'] = song.duration_ms,
        return json.dumps(js)

    @classmethod
    def standby_list_as_jsonlines(cls, songs: List['BriefSongModel']):
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


# For debugging.
if __name__ == '__main__':
    import os

    from feeluown.library import Library
    from feeluown.library.uri import resolve, Resolver
    from fuo_ytmusic.provider import provider as p1
    from fuo_qqmusic import provider as p2
    from fuo_netease import provider as p3

    logging.basicConfig(level=logging.DEBUG)

    library = Library()
    p1.setup_http_proxy('http://127.0.0.1:7890')
    library.register(p1)
    library.register(p2)
    library.register(p3)
    Resolver.library = library
    library.setup_ai(AI(
        # base_url='https://api.deepseek.com',
        # api_key=os.environ.get('DEEPSEEK_API_KEY'),
        # model='deepseek-chat',
        base_url='https://ark.cn-beijing.volces.com/api/v3',
        api_key=os.environ.get('ARK_API_KEY'),
        model='ep-20250202091715-vwjw2',
        # base_url='https://open.bigmodel.cn/api/paas/v4/',
        # api_key=os.environ.get('GLM_API_KEY'),
        # model='GLM-4-Air',
        # api_key=os.environ.get('MOONSHOT_API_KEY'),
        # base_url='https://api.moonshot.cn/v1',
        # model='moonshot-v1-8k',
    ))
    standby_text = '''\
fuo://qqmusic/songs/409175284   # "下雨天 - 鱼天邻制作" - 南拳妈妈 - "" - 00:51
fuo://qqmusic/songs/463631892   # 下雨天 (DJ阿智版) - 南拳妈妈 & DJ阿智 - "" - 01:28
fuo://qqmusic/songs/102697748   # 下雨天 - 南拳妈妈 - 优の良曲 南搞小孩 - 04:13
fuo://ytmusic/songs/XkcKycMblaE # 下雨天 - 芝麻Mochi - 下雨天 - 04:26
fuo://ytmusic/songs/F-YMyH74748 # 下雨天 - "" - 下雨天 - 04:14
fuo://ytmusic/songs/BBe-Zwb7ElM # Rainy Day (下雨天) - Nan Quan Mama - 優的良曲南搞小孩 - 04:14
fuo://netease/songs/1382202727  # 下雨天（翻自 南拳妈妈NQMM） - 33没事儿 - 翻唱 - 04:10
fuo://netease/songs/2135170282  # 下雨天（Alqas 版） - Kk - 南拳妈妈-下雨天 - 03:26
fuo://netease/songs/1905457762  # 下雨天（Cover 南拳妈妈） - 张贤静 - For you - 04:36
'''
    standby_list = []
    for line in standby_text.splitlines():
        l_nospace = line.strip()
        if l_nospace:
            standby_list.append(resolve(l_nospace))

    print(standby_text)

    matcher = AIStandbyMatcher(
        library.ai, library.a_song_prepare_media_no_exc, 60, '>>>')

    song = BriefSongModel(
        source='dummy',
        identifier='xxx',
        title='下雨天',
        artists_name='南拳妈妈'
    )
    pair = asyncio.run(matcher.match(song, standby_list))
    print(pair)
