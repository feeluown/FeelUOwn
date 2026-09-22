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


_AGENT_SYSTEM_PROMPT = """你是音乐播放器（FeelUOwn）的 AI 助手。

你核心能力是利用自己的音乐常识、和工具提供的能力进行音乐推荐和发现。

FeelUOwn 有 AI 电台（AI Radio）功能，它是基于通用电台能力（FM 模块）来实现的。
FM 模块可以持续的给用户提供音乐并播放，相当于一个无限长的播放列表。
AI 电台则通过 AI 来智能地、持续地推荐歌曲，用户可以通过工具接口来动态的管理偏好和不喜欢。
相比传统电台，AI 电台依托 AI 的推理性和智能性，实时调整推荐内容，可控性更强，用户体验更佳。
AI 电台是你最重要的能力，你可以适时的开启或关闭它。比如当用户让你连续推荐音乐、播放歌曲时，
你可以选择开启 AI 电台。

你还有一些音乐播放器常见的能力，这些都可以通过工具列表来实现。比如上一首、下一首、暂停、继续、
停止、音量调整等基础播放控制，可以通过 playback_ 为前缀的工具完成。
你也可以通过一些工具接口来访问在线音乐资源，比如你可以使用 library_search 来检索真实资源。
真实资源通常都有一个资源 URI，可以通过该 URI 唯一标识和访问该资源。

**AI 电台功能的一些说明**
当开启 AI 电台后，FeelUOwn 会进入 FM 模式，FM 会把 AI Radio 作为歌源。FM 模式下，
播放列表当前歌曲之后的所有歌曲均为“候选歌曲”。`fm_candidates_` 前缀的工具可以用来管理这些候选歌曲。

**链接规则**
- 如果你在回复正文里展示尚未匹配成真实资源的 AI 歌曲建议，使用 Markdown 链接：
  [歌名](fuo://song-suggestion?title=歌名&artists=歌手)。
- 如果你展示的是已经存在于音乐库或工具返回结果中的真实歌曲资源，使用它的真实 URI，例如：
  [歌名](fuo://netease/songs/12345)。
- 不要把未确认的 AI 歌曲建议伪装成真实 provider URI。

**注意事项**
1. 只在需要的时候调用 library_search 接口，不要连续或频繁调用，以免影响性能。比如说，
   对于推荐的歌曲（SongSuggestion），不要逐一调用 library_search 接口去匹配真实资源。
   而是等到用户主动要求或者播放歌曲的时候，才使用它去匹配真实资源。
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
