import logging
from typing import TYPE_CHECKING

from feeluown.library import BriefSongModel, reverse
from feeluown.library.text2song import analyze_text, AnalyzeError

try:
    from openai import OpenAI, AuthenticationError
except ImportError:
    AI_RADIO_SUPPORTED = False
else:
    AI_RADIO_SUPPORTED = True

if TYPE_CHECKING:
    from feeluown.app import App


logger = logging.getLogger(__name__)


def song2line(song: BriefSongModel):
    line = reverse(song, as_line=True)
    parts = line.split('#', 1)
    if len(parts) >= 2:
        return parts[1]
    return None


class AIRadio:
    def __init__(self, app: 'App'):
        self._app = app

        self._messages = []
        self._messages.append({"role": "system",
                               "content": self._app.config.AI_RADIO_PROMPT})

    def fetch_songs_func(self, _):
        client = OpenAI(
            api_key=self._app.config.OPENAI_API_KEY,
            base_url=self._app.config.OPENAI_API_BASEURL,
        )
        # NOTE(cosven): 经过一些手动测试，我发现“策略”对推荐结果影响很大。
        #
        # 目前的策略是使用多轮对话，让 AI 知道自己之前推荐过什么样的歌曲，
        # 来避免重复推荐。这样的效果是不错的。
        #
        # 尝试过，但效果不好的策略之一：即使把用户不喜欢的歌曲列表提供给 AI，
        # AI 仍然会推不喜欢的歌曲，所以这里不提供用户不喜欢的歌曲列表。所有的模型都这样。
        # 举个例子：kimi 和 deepseek 很喜欢推荐“田馥甄”的“小幸运”，即使我说自己不喜欢，
        # 它还是又很高概率推荐。可能需要一个更强大的 PROMPT :(
        self._messages.append({
            "role": "user",
            "content": (
                f"当前播放列表内容如下：\n{self.get_msg()}")
        })
        try:
            response = client.chat.completions.create(
                model=self._app.config.OPENAI_MODEL,
                messages=self._messages,
            )
        except AuthenticationError:
            logger.exception('AI authentication failed')
            return []
        except Exception:
            logger.exception('AI request failed')
            return []
        msg = response.choices[0].message
        self._messages.append(msg)
        for _msg in self._messages[-2:]:
            logger.info(f"AI radio, message: {dict(_msg)['content']}")
        try:
            songs, err_count = analyze_text(str(msg.content))
        except AnalyzeError:
            logger.exception('Analyze AI response failed')
            return []
        logger.info(f'AI recommend {len(songs)} songs, err_count={err_count}')
        return songs

    def get_msg(self):
        msg_lines = []
        for song in self._app.playlist.list():
            if self._app.playlist.is_bad(song):
                continue
            line = song2line(song)
            if line is not None:
                msg_lines.append(line)
        return '\n'.join(msg_lines)


# For debugging.
if __name__ == '__main__':
    import os
    from unittest.mock import MagicMock

    app = MagicMock()
    app.config.OPENAI_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    app.config.OPENAI_API_BASEURL = 'https://api.deepseek.com'
    app.config.OPENAI_MODEL = 'deepseek-chat'
    app.config.AI_RADIO_PROMPT = '''\
你是一个音乐推荐系统。你根据用户的歌曲列表分析用户的喜好，给用户推荐一些歌。默认推荐5首歌。

有几个注意点
1. 不要推荐与用户播放列表中一模一样的歌曲。不要推荐用户不喜欢的歌曲。不要重复推荐。
2. 你返回的内容只应该有 JSON，其它信息都不需要。也不要用 markdown 格式返回。
3. 你推荐的歌曲需要使用类似这样的 JSON 格式
    [{"title": "xxx", "artists": ["yyy", "zzz"], "description": "推荐理由"}]
'''
    radio = AIRadio(app)
    radio.get_msg = MagicMock(return_value='''
雨蝶 - 李翊君 - 经典再回首 - 03:52
海阔天空 - Beyond - 华纳超极品音色系列 - 03:59
等待 - 韩磊 - 帝王之声 - 03:39
向天再借五百年 - 韩磊 - 向天再借五百年 - 03:12
你是我的眼 - 萧煌奇 - 你是我的眼 - 05:21
''')
    songs = radio.fetch_songs_func(5)
    for song in songs:
        print(song)
