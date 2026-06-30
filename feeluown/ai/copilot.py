from typing import List
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langchain_core.callbacks import BaseCallbackHandler

from feeluown.app import App
from feeluown.ai.llm import create_chat_model_with_config
from feeluown.ai.matcher import SongSuggestionMatcher
from feeluown.ai.models import SongSuggestion
from feeluown.ai.playback import playback_tools
from feeluown.ai.radio import ai_radio_tools
from feeluown.library import BriefSongModel
from feeluown.utils.dispatch import Signal


@dataclass
class CopilotArtifact:
    """A structured UI artifact produced by AI tools."""

    identifier: int
    type: str
    title: str
    songs: List[SongSuggestion]


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

    def clear(self):
        self._artifacts.clear()


@dataclass
class CopilotContext:
    copilot: "Copilot"
    app: "App"


@tool
def play_song_suggestion(song: SongSuggestion, runtime: ToolRuntime):
    """Play a song suggestion.

    :param song: A SongSuggestion.
    """
    runtime.context.app.playlist.play_model(song.to_brief_song())


@tool
def create_song_suggestions_artifact(
    songs: List[SongSuggestion],
    runtime: ToolRuntime,
    title: str = "",
) -> bool:
    """Create an interactive artifact for song suggestions.

    Use this when you recommend multiple songs and want the user to inspect them
    in the AI assistant UI.

    :param songs: A list of SongSuggestion.
    :param title: Optional artifact title.
    """
    runtime.context.copilot.add_songs_artifact(songs, title=title)
    return True


tools = [
    play_song_suggestion,
    create_song_suggestions_artifact,
    *playback_tools,
    *ai_radio_tools,
]


_AGENT_SYSTEM_PROMPT = (
    "你是一个音乐播放器 AI 助手。"
    "当你向用户推荐或整理一组歌曲时，优先调用 create_song_suggestions_artifact "
    "工具创建可交互歌曲建议列表。"
    "上一首、下一首、暂停、继续、停止、音量调整等基础播放控制，"
    "应通过 playback_ 开头的工具完成。"
    "AI 电台开关、状态和偏好应优先通过 ai_radio_ 开头的工具完成，"
    "不要要求用户去其它界面操作。"
    "当用户要求开启、启动、进入 AI 电台时，调用 ai_radio_activate。"
    "当用户要求关闭、停止、退出 AI 电台时，调用 ai_radio_deactivate。"
    "当用户想查看或修改 FM 候选列表时，先调用 ai_radio_get_state。"
    "FM 候选歌曲指播放列表中当前播放歌曲后面的真实歌曲，"
    "不是 SongSuggestion，也不是正文中的 fuo://song-suggestion 链接。"
    "候选列表操作必须通过 fm_candidates_ 开头的工具完成。"
    "AI 电台和候选列表的命令型工具只返回是否成功；"
    "如果需要查看操作后的候选列表，继续调用 ai_radio_get_state。"
    "如果用户在 AI 电台未开启时提出使用或修改候选列表，先调用 ai_radio_activate，"
    "再根据用户需求继续操作；如果用户只是询问状态，请说明当前未开启。"
    "当用户反馈会影响后续 AI 电台推荐偏好时，调用 ai_radio_update_preferences。"
    "如果你在回复正文里展示尚未匹配成真实资源的 AI 歌曲建议，使用 Markdown 链接："
    "[歌名](fuo://song-suggestion?title=歌名&artists=歌手)。"
    "如果你展示的是已经存在于音乐库或工具返回结果中的真实歌曲资源，"
    "使用它的真实 URI，例如 [歌名](fuo://netease/songs/12345)。"
    "不要把未确认的 AI 歌曲建议伪装成真实 provider URI。"
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
        self._artifacts = ArtifactsManager()
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

    def get_artifacts(self) -> List[CopilotArtifact]:
        return self._artifacts.list()

    def get_config(self):
        return {
            "configurable": {"thread_id": str(self._current_thread_id)},
            "callbacks": [self._agent_stream_callback],
        }

    def get_current_thread_history_messages(self) -> List[BaseMessage]:
        return self._agent.get_state(self.get_config()).values["messages"]
