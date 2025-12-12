import datetime
from typing import List
from dataclasses import dataclass

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

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
class CopilotContext:
    copilot: 'Copilot'
    app: 'App'


@tool
def add_songs_to_playlist_candidates(
    songs: List[AISongModel], runtime: ToolRuntime
) -> bool:
    """Add songs to playlist candidates.

    :param songs: A list of AISongModel.
    """
    runtime.context.copilot.set_candidates(songs)


@tool
def play_song(song: AISongModel, runtime: ToolRuntime):
    """Play a song.

    :param song: A AISongModel.
    """
    runtime.context.app.playlist.play_model(song.to_brief_song())


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt="你是一个音乐播放器 AI 助手。",
        tools=[add_songs_to_playlist_candidates, play_song],
        context_schema=CopilotContext,
        checkpointer=InMemorySaver(),
    )


class AISongMatcher:
    def __init__(self, app: App):
        self._app = app

    async def match(self, ai_song: AISongModel) -> BriefSongModel:
        """Math a song by title and artists name.

        This API is in alpha stage.
        """
        title, artists_name = ai_song.title, ai_song.artists_name
        async for result in self._app.library.a_search(f'{title} {artists_name}'):
            if result is None:
                continue
            for song in result.songs:
                if (
                    song.title_display == title and
                    song.artists_name_display == artists_name
                ):
                    return song
        return None


class Copilot:
    def __init__(self, app: App):
        self._app = app
        self._agent = create_agent_with_config(app.config)
        self._agent_context = CopilotContext(copilot=self, app=app)
        self._candidates: List[AISongModel] = []
        self.candidates_changed = Signal()
        self._current_thread_id = 1

    def new_thread(self):
        self._current_thread_id += 1

    async def push_a_song(self) -> List[AISongModel]:
        await self._agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": await generate_prompt(self._app)
                    },
                    {
                        "role": "system",
                        "content": "给用户推荐1首歌。并将歌曲加入到播放列表候选中",
                    },
                ]
            },
            self._get_configurable(),
            context=self._agent_context,
        )
        return self._candidates

    async def astream_user_query(self, query: str):
        return self._agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            self._get_configurable(),
            stream_mode="messages",
            context=self._agent_context,
        )

    def set_candidates(self, ai_songs: List[AISongModel]):
        self._candidates = ai_songs
        self.candidates_changed.emit(ai_songs)

    def _get_configurable(self):
        return {"thread_id": str(self._current_thread_id)}


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

        copilot = Copilot(app)
        songs = asyncio.run(copilot.push_a_song())
        print(songs)
