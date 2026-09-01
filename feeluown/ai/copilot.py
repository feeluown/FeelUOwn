from typing import List
from dataclasses import dataclass

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langchain_core.callbacks import BaseCallbackHandler

from feeluown.app import App
from feeluown.ai.llm import create_chat_model_with_config
from feeluown.ai.matcher import SongSuggestionMatcher
from feeluown.ai.model_cache import ModelCache
from feeluown.ai.models import SongSuggestion
from feeluown.ai.tools import copilot_tools
from feeluown.library import (
    BaseModel,
    BriefSongModel,
)
from feeluown.utils.dispatch import Signal


ArtifactSong = SongSuggestion | BriefSongModel


@dataclass
class CopilotArtifact:
    """A structured UI artifact produced by AI tools."""

    identifier: int
    type: str
    title: str
    songs: List[ArtifactSong]


class ArtifactsManager:
    def __init__(self):
        self._artifacts: List[CopilotArtifact] = []
        self._next_artifact_id = 1
        self.added = Signal()

    def add_songs(
        self, songs: List[SongSuggestion], title: str = ""
    ) -> CopilotArtifact:
        artifact = CopilotArtifact(
            identifier=self._next_artifact_id,
            type="songs",
            title=title or "Songs",
            songs=songs,
        )
        self._next_artifact_id += 1
        self._artifacts.append(artifact)
        self.added.emit(artifact)
        return artifact

    def list(self) -> List[CopilotArtifact]:
        return list(self._artifacts)

    def get(self, identifier: int) -> CopilotArtifact | None:
        for artifact in self._artifacts:
            if artifact.identifier == identifier:
                return artifact
        return None

    def clear(self):
        self._artifacts.clear()


@dataclass
class CopilotContext:
    copilot: "Copilot"
    app: "App"


tools = copilot_tools


_AGENT_SYSTEM_PROMPT = """你是一个音乐播放器 AI 助手。

**音乐推荐能力**
当你向用户推荐或整理一组歌曲时，优先调用 create_song_suggestions_artifact 工具创建可交互歌曲建议列表。
SongSuggestion 是尚未匹配成 SongModel 的歌曲建议；不要把一组 SongSuggestion 一次性转换或播放。
create_song_suggestions_artifact 会清洗并校验歌曲建议；单个 artifact 最多包含 20 首。
play_song_suggestion 只用于“最新用户消息明确要求播放某一首建议歌曲”的场景。

**播放控制能力**
上一首、下一首、暂停、继续、停止、音量调整等基础播放控制，可以通过 playback_ 开头的工具完成。
播放真实歌曲资源时，调用 play_song_by_uri，传入歌曲 uri。

**在线音乐资源**
当用户要求搜索在线音乐资源时，优先使用 library_search 工具，并用 timeout 控制最长等待时间。
library_search 返回的 data.results 中的 uri 是真实资源 URI，可以在 Markdown 链接里使用。

**AI 电台**
AI 电台开关、状态和偏好应优先通过 ai_radio_ 开头的工具完成，不要要求用户去其它界面操作。
AI 电台只是激活 FM 模式的一种方式；FeelUOwn 也可以通过歌曲电台等其它方式进入 FM 模式。

**FM 候选列表**
FM 候选歌曲指播放列表中当前播放歌曲后面的真实歌曲。
FM 候选列表和 AI 电台是否开启无直接关系。
查看 FM 候选列表时调用 fm_candidates_get_state。
修改 FM 候选列表时只使用 fm_candidates_remove 和 fm_candidates_append。
fm_candidates_append 接收真实歌曲 URI 列表，fm_candidates_append 一次最多追加 3 首真实歌曲；不建议连续多次追加。

**链接规则**
- 如果你在回复正文里展示尚未匹配成真实资源的 AI 歌曲建议，使用 Markdown 链接：
  [歌名](fuo://song-suggestion?title=歌名&artists=歌手)。
- 如果你展示的是已经存在于音乐库或工具返回结果中的真实歌曲资源，使用它的真实 URI，例如：
  [歌名](fuo://netease/songs/12345)。
- 不要把未确认的 AI 歌曲建议伪装成真实 provider URI。
"""


def create_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt=_AGENT_SYSTEM_PROMPT,
        tools=tools,
        context_schema=CopilotContext,
        checkpointer=InMemorySaver(),
    )


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
        self._extra_callbacks = []
        self._artifacts = ArtifactsManager()
        self._model_cache = ModelCache(getattr(app, "library", None))
        self.artifact_added = self._artifacts.added
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
        self._model_cache = ModelCache(getattr(self._app, "library", None))

    def add_callback(self, callback):
        """Register an extra callback handler for agent invocations."""
        self._extra_callbacks.append(callback)

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

    def add_songs_artifact(
        self, songs: List[SongSuggestion], title: str = ""
    ) -> CopilotArtifact:
        return self._artifacts.add_songs(songs, title=title)

    def cache_model(self, model: BaseModel):
        self._model_cache.set_model(model)

    def get_model_by_uri(self, uri: str) -> BaseModel:
        return self._model_cache.get(uri)

    def get_song_by_uri(self, uri: str) -> BriefSongModel:
        model = self.get_model_by_uri(uri)
        assert isinstance(model, BriefSongModel)
        return model

    def get_artifacts(self) -> List[CopilotArtifact]:
        return self._artifacts.list()

    def get_artifact(self, identifier: int) -> CopilotArtifact | None:
        return self._artifacts.get(identifier)

    def get_artifact_song(
        self, artifact_id: int, song_position: int
    ) -> ArtifactSong | None:
        artifact = self.get_artifact(artifact_id)
        if artifact is None:
            return None
        if not 1 <= song_position <= len(artifact.songs):
            return None
        return artifact.songs[song_position - 1]

    def get_config(self):
        return {
            "configurable": {"thread_id": str(self._current_thread_id)},
            "callbacks": [self._agent_stream_callback, *self._extra_callbacks],
        }

    def get_current_thread_history_messages(self) -> List[BaseMessage]:
        return self._agent.get_state(self.get_config()).values["messages"]
