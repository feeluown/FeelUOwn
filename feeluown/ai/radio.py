import datetime
from typing import List
from dataclasses import dataclass

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

from feeluown.app import App
from feeluown.library import BriefSongModel, ModelState
from feeluown.ai.prompt import generate_prompt_for_library
from feeluown.utils.dispatch import Signal


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


def create_chat_model_with_config(config):
    return init_chat_model(
        config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_API_BASEURL,
        temperature=0,
        model_provider="openai",  # OpenAI compatible API
    )


@dataclass
class RadioContext:
    radio: 'AIRadio'


@tool
def add_songs_to_ai_radio_candidates(
    songs: List[AISongModel], runtime: ToolRuntime
) -> bool:
    """Add songs to ai radio candidates.

    :param songs: A list of AISongModel.
    """
    runtime.context.radio.set_candidates(songs)


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt=config.AI_RADIO_PROMPT,
        tools=[add_songs_to_ai_radio_candidates],
        context_schema=RadioContext,
    )


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
    """
    AI Radio 是一个用户可控制的智能音乐电台，这会创造一个前所未有的音乐体验。
    传统的音乐电台（如各平台的私人推荐）会按照平台自己的固有算法来推荐音乐，
    而它只有 like 和 dislike 两种反馈方式，很难完整反应用户当下感受与反馈。
    AI Radio 允许用户注入自然语言来调整推荐算法，实现可交互式的智能音乐推荐。
    """

    def __init__(self, app: App):
        self._app = app
        self._agent = create_agent_with_config(app.config)
        self._agent_context = RadioContext(radio=self)
        self._candidates: List[AISongModel] = []
        self.candidates_changed = Signal()

    async def get5songs(self) -> List[AISongModel]:
        await self._agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": await generate_prompt(self._app)
                    },
                    {
                        "role": "system",
                        "content": "给用户推荐5首歌。并将歌曲加入到电台候选中",
                    },
                ]
            },
            context=self._agent_context,
        )
        return self._candidates

    def set_candidates(self, ai_songs: List[AISongModel]):
        self._candidates = ai_songs
        self.candidates_changed.emit(ai_songs)


async def generate_prompt(app: App):
    """
    1. Today's date and current time.
    2. User's music library, including songs, albums, artists, playlists.
    """
    time_prompt = f"当前时间是 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
    library_prompt = await generate_prompt_for_library(app.coll_mgr.get_coll_library())
    return f"{time_prompt}\n\n{library_prompt}"


if __name__ == "__main__":
    import os
    import asyncio

    from feeluown.debug import mock_app

    with mock_app() as app:
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
