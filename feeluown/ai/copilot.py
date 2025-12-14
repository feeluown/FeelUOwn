import datetime
from typing import List
from dataclasses import dataclass

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langchain_core.callbacks import BaseCallbackHandler

from feeluown.app import App
from feeluown.library import BriefSongModel, ModelState
from feeluown.ai.prompt import generate_prompt_for_library
from feeluown.utils.dispatch import Signal


@dataclass
class AISongModel:
    """A song recommended by the AI.

    :param description: Recommendation reason or song description.
    """

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


tools = [add_songs_to_playlist_candidates, play_song]


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt="你是一个音乐播放器 AI 助手。",
        tools=tools,
        context_schema=CopilotContext,
        checkpointer=InMemorySaver(),
    )


def create_recommendation_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt="你是一个音乐播放器 AI 助手。",
        tools=tools,
        context_schema=CopilotContext,
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


class AgentStreamCallback(BaseCallbackHandler):
    def __init__(self, copilot: 'Copilot', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__copilot = copilot

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.__copilot.is_working = True

    def on_chain_end(self, outputs, **kwargs):
        self.__copilot.is_working = False

    def on_chain_error(self, error, **kwargs):
        self.__copilot.is_working = False


class Copilot:
    def __init__(self, app: App):
        self._app = app
        self._agent = create_agent_with_config(self._app.config)
        self._agent_context = CopilotContext(copilot=self, app=app)
        self._agent_stream_callback = AgentStreamCallback(self)
        self._candidates: List[AISongModel] = []
        self.candidates_changed = Signal()
        self._current_thread_id = 1
        # Agent is working or not
        # When the agent is streaming messages, it is working.
        self._is_working = False
        # emit(bool): working: true, not_working: false
        self.working_state_changed = Signal()

    @property
    def is_working(self) -> bool:
        return self._is_working

    @is_working.setter
    def is_working(self, working: bool):
        self._is_working = working
        self.working_state_changed.emit(working)

    def new_thread(self):
        self._current_thread_id += 1

    async def recommend_a_song(self) -> List[AISongModel]:
        """Create an adhoc agent to recommend a song.

        :return: A list of AISongModel.
        """
        agent = create_recommendation_agent_with_config(self._app.config)
        input = {
            "messages": [
                {
                    "role": "system",
                    "content": await generate_prompt(self._app)
                },
                {
                    "role": "system",
                    "content": ("根据用户的音乐库收藏，分析用户的喜好，并且综合当前日期/时间等信息，"
                                "推荐1首合适的歌给用户，并将歌曲加入到播放列表候选中。"),
                },
            ]
        }
        await agent.ainvoke(
            input,
            context=self._agent_context,
        )
        return self._candidates

    async def astream_user_query(self, query: str):
        async for v in self._agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            self.get_config(),
            stream_mode="messages",
            context=self._agent_context,
        ):
            yield v

    def set_candidates(self, ai_songs: List[AISongModel]):
        self._candidates = ai_songs
        self.candidates_changed.emit(ai_songs)

    def get_config(self):
        return {
            "configurable": {"thread_id": str(self._current_thread_id)},
            # "callbacks": [self._agent_stream_callback],
        }

    def get_current_thread_history_messages(self) -> List[BaseMessage]:
        return self._agent.get_state(self.get_config()).values['messages']


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

        copilot = Copilot(app)
        songs = asyncio.run(copilot.recommend_a_song())
        state = copilot._agent.get_state(copilot.get_config())
