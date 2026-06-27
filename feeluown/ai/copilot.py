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
from feeluown.library import (
    BriefSongModel,
    ModelState,
    get_standby_score,
    STANDBY_FULL_SCORE,
    STANDBY_DEFAULT_MIN_SCORE,
)
from feeluown.ai.prompt import generate_prompt_for_library
from feeluown.utils.dispatch import Signal


@dataclass
class SongSuggestion:
    """A song suggested by the AI before it is matched to a provider song.

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


@dataclass
class CopilotArtifact:
    """A structured UI artifact produced by AI tools."""

    identifier: int
    type: str
    title: str
    songs: List[SongSuggestion]
    view: str = "list"


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
    copilot: "Copilot"
    app: "App"


@tool
def add_songs_to_playlist_candidates(
    songs: List[SongSuggestion], runtime: ToolRuntime
) -> bool:
    """Add songs to playlist candidates.

    :param songs: A list of SongSuggestion.
    """
    runtime.context.copilot.set_candidates(songs)


@tool
def play_song(song: SongSuggestion, runtime: ToolRuntime):
    """Play a song.

    :param song: A SongSuggestion.
    """
    runtime.context.app.playlist.play_model(song.to_brief_song())


@tool
def create_song_suggestions_artifact(
    songs: List[SongSuggestion],
    runtime: ToolRuntime,
    title: str = "",
    view: str = "list",
) -> bool:
    """Create an interactive artifact for song suggestions.

    Use this when you recommend multiple songs and want the user to inspect them
    in the AI assistant UI.

    :param songs: A list of SongSuggestion.
    :param title: Optional artifact title.
    :param view: Preferred display mode. Current supported value is "list".
    """
    runtime.context.copilot.add_songs_artifact(songs, title=title, view=view)
    return True


tools = [add_songs_to_playlist_candidates, play_song, create_song_suggestions_artifact]


_AGENT_SYSTEM_PROMPT = (
    "你是一个音乐播放器 AI 助手。"
    "当你向用户推荐或整理一组歌曲时，优先调用 create_song_suggestions_artifact "
    "工具创建可交互歌曲建议列表。"
    "如果你在回复正文里展示歌曲标题，可以使用 Markdown 链接："
    "[歌名](fuo://song-suggestion?title=歌名&artists=歌手)。"
)


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt=_AGENT_SYSTEM_PROMPT,
        tools=tools,
        context_schema=CopilotContext,
        checkpointer=InMemorySaver(),
    )


def create_recommendation_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt="你是一个音乐播放器 AI 助手。",
        tools=[add_songs_to_playlist_candidates],
        context_schema=CopilotContext,
    )


class SongSuggestionMatcher:
    def __init__(self, app: App):
        self._app = app

    async def match(self, suggestion: SongSuggestion) -> BriefSongModel:
        """Match a suggested song by title and artists name.

        This API is in alpha stage.
        """
        origin = suggestion.to_brief_song()
        title, artists_name = suggestion.title, suggestion.artists_name
        candidates = []
        async for result in self._app.library.a_search(f"{title} {artists_name}"):
            if result is None:
                continue
            for standby in result.songs:
                score = get_standby_score(origin, standby)
                if score == STANDBY_FULL_SCORE:
                    return standby
                elif score >= STANDBY_DEFAULT_MIN_SCORE:
                    candidates.append((score, standby))
        sorted_candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
        return sorted_candidates[0][1] if sorted_candidates else None


class AgentStreamCallback(BaseCallbackHandler):
    def __init__(self, copilot: "Copilot", *args, **kwargs):
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
        self._candidates: List[SongSuggestion] = []
        self.candidates_changed = Signal()
        self._artifacts: List[CopilotArtifact] = []
        self._next_artifact_id = 1
        self.artifact_added = Signal()
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
        self._artifacts.clear()

    async def recommend_songs(
        self, count: int, instructions: List[str] | None = None
    ) -> List[SongSuggestion]:
        """Create an adhoc agent to recommend songs.

        :return: A list of SongSuggestion.
        """
        count = max(1, count)
        self.set_candidates([])
        agent = create_recommendation_agent_with_config(self._app.config)
        user_instructions = "\n".join(
            f"- {instruction}" for instruction in instructions or []
        )
        instruction_prompt = (
            f"用户希望 AI 电台接下来的推荐满足以下要求：\n{user_instructions}\n"
            if user_instructions
            else ""
        )
        input = {
            "messages": [
                {
                    "role": "system",
                    "content": self._app.config.AI_RADIO_PROMPT,
                },
                {"role": "system", "content": await generate_prompt(self._app)},
                {
                    "role": "system",
                    "content": (
                        f"{instruction_prompt}"
                        "根据用户的音乐库收藏，分析用户的喜好，并且综合当前日期/时间等信息，"
                        f"推荐{count}首适合继续播放的歌给用户，"
                        "并将歌曲加入到播放列表候选中。"
                    ),
                },
            ]
        }
        await agent.ainvoke(
            input,
            context=self._agent_context,
        )
        return self._candidates

    async def recommend_a_song(self) -> List[SongSuggestion]:
        """Create an adhoc agent to recommend a song.

        :return: A list of SongSuggestion.
        """
        return await self.recommend_songs(1)

    async def match_song_suggestion(
        self, suggestion: SongSuggestion
    ) -> BriefSongModel | None:
        matcher = SongSuggestionMatcher(self._app)
        return await matcher.match(suggestion)

    async def astream_user_query(self, query: str):
        async for v in self._agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            self.get_config(),
            stream_mode="messages",
            context=self._agent_context,
        ):
            yield v

    def set_candidates(self, suggestions: List[SongSuggestion]):
        self._candidates = suggestions
        self.candidates_changed.emit(suggestions)

    def add_songs_artifact(
        self, songs: List[SongSuggestion], title: str = "", view: str = "list"
    ) -> CopilotArtifact:
        artifact = CopilotArtifact(
            identifier=self._next_artifact_id,
            type="songs",
            title=title or "Songs",
            songs=songs,
            view=view,
        )
        self._next_artifact_id += 1
        self._artifacts.append(artifact)
        self.artifact_added.emit(artifact)
        return artifact

    def get_artifacts(self) -> List[CopilotArtifact]:
        return list(self._artifacts)

    def get_config(self):
        return {
            "configurable": {"thread_id": str(self._current_thread_id)},
            "callbacks": [self._agent_stream_callback],
        }

    def get_current_thread_history_messages(self) -> List[BaseMessage]:
        return self._agent.get_state(self.get_config()).values["messages"]


async def generate_prompt(app: App):
    """
    1. Today's date and current time.
    2. User's music library, including songs, albums, artists, playlists.
    """
    time_prompt = (
        f"当前时间是 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
    )
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
