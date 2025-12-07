from dataclasses import dataclass
from typing import List

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from langchain_core.callbacks.base import BaseCallbackHandler

from feeluown.app import App
from feeluown.ai.prompt import generate_prompt_for_library
from feeluown.utils.dispatch import Signal

checkpointer = InMemorySaver()


@dataclass
class AISongModel:
    """A song recommended by the agent."""
    title: str
    artists_name: str
    description: str


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
def add_songs_to_ai_radio_candidates(songs: List[AISongModel], runtime: ToolRuntime) -> bool:
    """Add songs to ai radio candidates.

    :param songs: A list of AISongModel.
    """
    runtime.context.candidates = songs


class AIRadio:
    default_prompt = '''\
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
'''

    def __init__(self, app: App):
        app.config.AI_RADIO_PROMPT = self.default_prompt
        self.agent = create_agent_with_config(app.config)
        self._context = Context(candidates=[])

    async def get5songs(self):
        agent = self.agent
        r1 = await agent.ainvoke(
            {"messages": [
                {"role": "system", "content": await generate_prompt(app)},
                {"role": "system", "content": '给用户推荐5首歌'},
            ]},
            context=self._context
        )
        for message in r1['messages']:
            print(message)

        r2 = await agent.ainvoke(
            {"messages": [{"role": "system", "content": '将歌曲加入到电台候选中'}]},
            context=self._context
        )
        for message in r2['messages']:
            print(message)

        print(self._context.candidates)


async def generate_prompt(app: App):
    """
    1. Today's date and current time.
    2. User's music library, including songs, albums, artists, playlists.
    """
    import datetime

    time_prompt = f'当前时间是 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}。'
    library_prompt = await generate_prompt_for_library(app.coll_mgr.get_coll_library())
    return f'{time_prompt}\n\n{library_prompt}'


if __name__ == '__main__':
    import os
    import asyncio
    from unittest.mock import MagicMock

    app = MagicMock()
    app.config.OPENAI_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    app.config.OPENAI_API_BASEURL = 'https://api.deepseek.com'
    app.config.OPENAI_MODEL = 'deepseek-chat'

    app.config.OPENAI_API_KEY = os.environ.get('OPENROUTER_API_KEY_BAK', '')
    app.config.OPENAI_API_BASEURL = 'https://openrouter.ai/api/v1'
    app.config.OPENAI_MODEL = 'z-ai/glm-4.5-air:free'
    app.config.OPENAI_MODEL = 'kwaipilot/kat-coder-pro:free'

    ai_radio = AIRadio(app)
    asyncio.run(ai_radio.get5songs())
