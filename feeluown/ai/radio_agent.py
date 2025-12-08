from dataclasses import dataclass
from typing import List

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

from feeluown.app import App
from feeluown.library import BriefSongModel, ModelState
from feeluown.ai.prompt import generate_prompt_for_library

checkpointer = InMemorySaver()


@dataclass
class AISongModel:
    """A song recommended by the agent."""

    title: str
    artists_name: str
    description: str

    def to_brief_song(self) -> BriefSongModel:
        return BriefSongModel(
            state=ModelState.not_exists,
            source="ai",
            identifier="not-exists",
            title=self.title,
            artists_name=self.artists_name,
        )


@dataclass
class Context:
    candidates: List[AISongModel]


def create_chat_model_with_config(config):
    return init_chat_model(
        config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_API_BASEURL,
        temperature=0,
        model_provider="openai",  # OpenAI compatible API
    )


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt=config.AI_RADIO_PROMPT,
        tools=[add_songs_to_ai_radio_candidates],
        context_schema=Context,
        # checkpointer=checkpointer
    )


@tool
def add_songs_to_ai_radio_candidates(
    songs: List[AISongModel], runtime: ToolRuntime
) -> bool:
    """Add songs to ai radio candidates.

    :param songs: A list of AISongModel.
    """
    runtime.context.candidates = songs


class AISongMatcher:
    def __init__(self, app: App):
        self._app = app

    async def match(self, ai_song: AISongModel) -> BriefSongModel:
        brief_song = ai_song.to_brief_song()
        song_media_list = await self._app.library.a_list_song_standby_v2(
            brief_song, audio_select_policy=self._app.config.AUDIO_SELECT_POLICY
        )
        if song_media_list:
            song, media = song_media_list[0]
            return song
        return None


class AIRadio:
    default_prompt = """\
你是一个音乐推荐 AI Agent。

你根据用户的歌曲列表分析用户的喜好，给用户推荐一些歌。

推荐的基本规则：
1. 不要推荐与用户播放列表中一模一样的歌曲。
2. 不要推荐用户明确表示不喜欢的歌曲。
3. 不要重复推荐。

你可以自己思考一些推荐策略，也可以参考下面的推荐策略
1. 今天是否是某个特殊的日子（如节日等），如果是，可以推荐一些应景的歌曲。
2. 根据用户喜欢的歌手，推荐一些相似风格的歌手的歌曲。
3. 根据用户喜欢的歌曲的年代，推荐一些同年代的热门歌曲。
4. 根据用户喜欢的歌曲的类型，推荐一些相似类型的歌曲。
5. 推荐的时候适当考虑多样性
"""

    def __init__(self, app: App):
        self._app = app
        app.config.AI_RADIO_PROMPT = self.default_prompt
        self.agent = create_agent_with_config(app.config)
        self._context = Context(candidates=[])

    async def get5songs(self) -> List[AISongModel]:
        agent = self.agent
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "system", "content": await generate_prompt(self._app)},
                    {
                        "role": "system",
                        "content": "给用户推荐5首歌。并将歌曲加入到电台候选中",
                    },
                ]
            },
            context=self._context,
        )
        return self._context.candidates


async def generate_prompt(app: App):
    """
    1. Today's date and current time.
    2. User's music library, including songs, albums, artists, playlists.
    """
    import datetime

    time_prompt = (
        f"当前时间是 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
    )
    library_prompt = await generate_prompt_for_library(app.coll_mgr.get_coll_library())
    return f"{time_prompt}\n\n{library_prompt}"


if __name__ == "__main__":
    import os
    import asyncio
    from unittest.mock import MagicMock

    app = MagicMock()
    app.config.OPENAI_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    app.config.OPENAI_API_BASEURL = "https://api.deepseek.com"
    app.config.OPENAI_MODEL = "deepseek-chat"

    app.config.OPENAI_API_KEY = os.environ.get("OPENROUTER_API_KEY_BAK", "")
    app.config.OPENAI_API_BASEURL = "https://openrouter.ai/api/v1"
    app.config.OPENAI_MODEL = "z-ai/glm-4.5-air:free"
    app.config.OPENAI_MODEL = "kwaipilot/kat-coder-pro:free"

    ai_radio = AIRadio(app)
    songs = asyncio.run(ai_radio.get5songs())
    print(songs)
