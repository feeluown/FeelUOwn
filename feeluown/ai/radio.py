import datetime
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

from feeluown.ai.llm import create_chat_model_with_config
from feeluown.ai.matcher import SongSuggestionMatcher
from feeluown.ai.models import SongSuggestion
from feeluown.ai.prompt import generate_prompt_for_library
from feeluown.i18n import t
from feeluown.player.playlist import PlaylistMode
from feeluown.serializers import serialize
from feeluown.utils.dispatch import Signal

if TYPE_CHECKING:
    from feeluown.app import App
    from feeluown.library import BriefSongModel


logger = logging.getLogger(__name__)


DEFAULT_CANDIDATE_BATCH_SIZE = 3


def _get_active_ai_radio(runtime: ToolRuntime):
    ai = runtime.context.app.ai
    if ai is None:
        return None
    return ai.get_active_radio()


def _get_fm_candidates(runtime: ToolRuntime):
    return runtime.context.app.fm.candidates


def _ai_radio_status_result(
    ok: bool,
    message: str,
    action: str = "",
    error_code: str = "",
) -> dict:
    result = {
        "ok": ok,
        "active": False,
        "candidates": [],
        "candidate_count": 0,
        "message": message,
    }
    if action:
        result["action"] = action
    if error_code:
        result["error_code"] = error_code
    return result


def _ai_radio_inactive_result():
    return _ai_radio_status_result(
        ok=False,
        error_code="AI_RADIO_INACTIVE",
        message="AI Radio is not active.",
    )


def _ai_radio_unavailable_result():
    return _ai_radio_status_result(
        ok=False,
        error_code="AI_UNAVAILABLE",
        message="AI is not available.",
    )


@dataclass
class AIRadioRecommendationContext:
    suggestions: list[SongSuggestion]


@dataclass
class AIRadioState:
    active: bool
    candidate_batch_size: int
    current_song: Optional["BriefSongModel"] = None
    candidates: list["BriefSongModel"] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    avoidances: list[str] = field(default_factory=list)
    preference_notes: list[str] = field(default_factory=list)

    def to_ai_dict(self):
        return {
            "active": self.active,
            "current_song": (
                song_to_ai_dict(self.current_song)
                if self.current_song is not None
                else None
            ),
            "candidates": [
                song_to_ai_dict(song, position)
                for position, song in enumerate(self.candidates, start=1)
            ],
            "candidate_count": len(self.candidates),
            "candidate_batch_size": self.candidate_batch_size,
            "preferences": self.preferences,
            "avoidances": self.avoidances,
            "preference_notes": self.preference_notes,
        }


def song_to_ai_dict(song: "BriefSongModel", position: int | None = None):
    data = serialize("python", song)
    data["source"] = data.pop("provider", data.get("source"))
    data.pop("__type__", None)
    if position is not None:
        data["position"] = position
    return data


@tool
def collect_ai_radio_suggestions(
    songs: list[SongSuggestion],
    runtime: ToolRuntime,
) -> bool:
    """Collect song suggestions for AI radio playback.

    :param songs: A list of SongSuggestion.
    """
    runtime.context.suggestions = songs
    return True


def create_recommendation_agent_with_config(config):
    model = create_chat_model_with_config(config)
    return create_agent(
        model=model,
        system_prompt="你是一个音乐播放器 AI 电台推荐助手。",
        tools=[collect_ai_radio_suggestions],
        context_schema=AIRadioRecommendationContext,
    )


async def generate_prompt(app: "App"):
    """
    1. Today's date and current time.
    2. User's music library, including songs, albums, artists, playlists.
    """
    time_prompt = (
        f"当前时间是 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
    )
    library_prompt = await generate_prompt_for_library(app.coll_mgr.get_coll_library())
    return f"{time_prompt}\n\n{library_prompt}"


@tool
def ai_radio_activate(runtime: ToolRuntime, reset: bool = True) -> bool:
    """Activate AI Radio.

    This switches the playlist into FM mode and lets the current AI radio
    session provide future candidate songs.

    :param reset: Whether to reset the current playlist when entering FM mode.
    """
    app = runtime.context.app
    if app.ai is None:
        return False

    radio = app.ai.get_active_radio()
    if radio is not None:
        return True

    app.ai.activate_radio(reset=reset)
    return True


@tool
def ai_radio_deactivate(runtime: ToolRuntime) -> bool:
    """Deactivate AI Radio and leave playlist FM mode."""
    app = runtime.context.app
    if app.ai is None:
        return False
    app.ai.deactivate_radio()
    return True


@tool
def ai_radio_get_state(runtime: ToolRuntime) -> dict:
    """Get current AI radio state and upcoming candidate songs."""
    if runtime.context.app.ai is None:
        return _ai_radio_unavailable_result()
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return _ai_radio_inactive_result()
    return {"ok": True, **radio.get_state_for_ai()}


@tool
def fm_candidates_clear(runtime: ToolRuntime) -> bool:
    """Clear all upcoming FM candidate songs while AI Radio is active."""
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    radio.set_candidate_status(t("ai-radio-candidates-clearing"))
    ok = _get_fm_candidates(runtime).clear()
    radio.set_candidate_status(t("ai-radio-candidates-cleared"))
    return ok


@tool
def fm_candidates_remove(positions: list[int], runtime: ToolRuntime) -> bool:
    """Remove upcoming FM candidate songs by 1-based positions.

    :param positions: 1-based candidate positions to remove.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    fm_candidates = _get_fm_candidates(runtime)
    old_candidates = fm_candidates.list_candidates()
    remove_positions = _normalize_positions(positions, len(old_candidates))
    ok = fm_candidates.remove(positions)
    removed_count = len(remove_positions) if ok else 0
    radio.set_candidate_status(
        t("ai-radio-candidates-updated", count=removed_count)
    )
    return ok


@tool
def fm_candidates_keep(positions: list[int], runtime: ToolRuntime) -> bool:
    """Keep only selected upcoming FM candidates by 1-based positions.

    :param positions: 1-based candidate positions to keep.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    ok = _get_fm_candidates(runtime).keep(positions)
    radio.set_candidate_status(t("ai-radio-candidates-kept"))
    return ok


@tool
async def fm_candidates_append(
    songs: list[SongSuggestion], runtime: ToolRuntime
) -> bool:
    """Append song suggestions to the FM candidate list.

    The input songs are AI song suggestions, not playlist candidates yet. This
    tool conservatively matches at most the radio batch size into real provider
    songs, then appends those real songs as upcoming FM candidates.

    :param songs: Suggested songs to match and append.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    fm_candidates = _get_fm_candidates(runtime)
    matched_songs = await radio.match_suggestions(songs)
    old_candidates = fm_candidates.list_candidates()
    if matched_songs:
        radio.set_candidate_status(
            t("ai-radio-candidates-adding", count=len(matched_songs))
        )
        ok = fm_candidates.append(matched_songs)
        candidates = fm_candidates.list_candidates()
        added_count = len(candidates) - len(old_candidates) if ok else 0
        radio.set_candidate_status(
            t("ai-radio-candidates-updated", count=added_count)
        )
    else:
        ok = fm_candidates.append([])
        radio.set_candidate_status(t("ai-radio-candidates-update-failed"))
    return ok


@tool
async def fm_candidates_replace(
    songs: list[SongSuggestion],
    runtime: ToolRuntime,
    keep_positions: list[int] | None = None,
) -> bool:
    """Replace FM candidates, optionally keeping selected 1-based positions.

    FM candidates are real songs already in the playlist after the current song.
    The input songs are AI song suggestions to match into new real candidates.

    :param songs: Suggested songs to match and append.
    :param keep_positions: Existing 1-based candidate positions to preserve.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    fm_candidates = _get_fm_candidates(runtime)
    matched_songs = await radio.match_suggestions(songs)
    candidates_count = len(fm_candidates.list_candidates())
    keep_positions = _normalize_positions(keep_positions or [], candidates_count)
    if matched_songs:
        radio.set_candidate_status(
            t("ai-radio-candidates-adding", count=len(matched_songs))
        )
        ok = fm_candidates.replace(
            matched_songs, keep_positions=keep_positions
        )
        candidates = fm_candidates.list_candidates()
        added_count = max(0, len(candidates) - len(keep_positions)) if ok else 0
        radio.set_candidate_status(
            t("ai-radio-candidates-updated", count=added_count)
        )
    else:
        ok = fm_candidates.replace([], keep_positions=keep_positions)
        radio.set_candidate_status(t("ai-radio-candidates-update-failed"))
    return ok


@tool
def ai_radio_update_preferences(
    runtime: ToolRuntime,
    preferences: list[str] | None = None,
    avoidances: list[str] | None = None,
    reason: str = "",
) -> bool:
    """Update current-session AI radio preferences.

    Use this when the user gives feedback that should affect future automatic
    AI radio recommendations.

    :param preferences: Musical traits the user wants more of.
    :param avoidances: Musical traits the user wants less of.
    :param reason: Short reason derived from the user's feedback.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return False
    return radio.update_preferences(
        preferences=preferences or [],
        avoidances=avoidances or [],
        reason=reason,
    )


ai_radio_tools = [
    ai_radio_activate,
    ai_radio_deactivate,
    ai_radio_get_state,
    fm_candidates_clear,
    fm_candidates_remove,
    fm_candidates_keep,
    fm_candidates_append,
    fm_candidates_replace,
    ai_radio_update_preferences,
]


class AIRadioRecommender:
    def __init__(
        self,
        app: "App",
        set_status,
        matcher_cls=None,
        recommendation_agent_factory=None,
        candidate_batch_size=DEFAULT_CANDIDATE_BATCH_SIZE,
    ):
        self._app = app
        self._set_status = set_status
        self._matcher_cls = matcher_cls
        self._recommendation_agent_factory = (
            recommendation_agent_factory or create_recommendation_agent_with_config
        )
        self._candidate_batch_size = candidate_batch_size
        self._thread_id = 1
        self._preferences = []
        self._avoidances = []
        self._preference_notes = []
        self._seen_songs = set()

    @property
    def candidate_batch_size(self) -> int:
        return self._candidate_batch_size

    @property
    def preferences(self) -> list[str]:
        return list(self._preferences)

    @property
    def avoidances(self) -> list[str]:
        return list(self._avoidances)

    @property
    def preference_notes(self) -> list[str]:
        return list(self._preference_notes)

    def update_preferences(
        self,
        preferences: list[str] | None = None,
        avoidances: list[str] | None = None,
        reason: str = "",
    ) -> bool:
        self._preferences.extend(_clean_texts(preferences or []))
        self._avoidances.extend(_clean_texts(avoidances or []))
        if reason.strip():
            self._preference_notes.append(reason.strip())
        self._set_status(t("ai-radio-instruction-updated"))
        return True

    async def recommend_matched_songs(self, number: int, radio_state: dict):
        number = self.normalize_fetch_count(number)

        try:
            self._set_status(t("ai-radio-candidates-requesting", count=number))
            suggestions = await self.recommend_suggestions(number, radio_state)
        except Exception:  # noqa
            logger.exception("AI radio failed to recommend songs")
            return []

        matched = await self.match_suggestions(
            suggestions,
            count=number,
            limit_processed=False,
        )
        return matched

    async def recommend_suggestions(
        self, count: int, radio_state: dict | None = None
    ) -> list[SongSuggestion]:
        """Recommend songs for AI radio without matching provider resources."""
        count = self.normalize_fetch_count(count)
        agent = self._recommendation_agent_factory(self._app.config)
        context = AIRadioRecommendationContext(suggestions=[])
        radio_state = radio_state or {}
        preferences = "\n".join(
            f"- {item}" for item in radio_state.get("preferences", [])
        )
        avoidances = "\n".join(
            f"- {item}" for item in radio_state.get("avoidances", [])
        )
        notes = "\n".join(
            f"- {item}" for item in radio_state.get("preference_notes", [])
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
                        "AI 电台当前状态：\n"
                        f"{radio_state}\n"
                        "用户偏好：\n"
                        f"{preferences or '- 暂无'}\n"
                        "用户想避免：\n"
                        f"{avoidances or '- 暂无'}\n"
                        "近期反馈摘要：\n"
                        f"{notes or '- 暂无'}\n"
                        "根据用户的音乐库收藏，分析用户的喜好，并且综合当前日期/时间等信息，"
                        f"推荐{count}首适合继续播放的歌给用户，"
                        "并调用 collect_ai_radio_suggestions 生成歌曲建议列表。"
                    ),
                },
            ]
        }
        await agent.ainvoke(
            input,
            self.get_agent_config(),
            context=context,
        )
        return context.suggestions

    def get_agent_config(self):
        return {
            "configurable": {"thread_id": f"ai-radio-{self._thread_id}"},
        }

    async def match_suggestions(
        self,
        suggestions: list["SongSuggestion"],
        count: int | None = None,
        limit_processed: bool = True,
    ):
        count = self.normalize_fetch_count(count or len(suggestions) or 1)
        suggestions_to_process = (
            suggestions[:count] if limit_processed else suggestions
        )
        songs = []
        matcher = self._create_matcher()
        for suggestion in suggestions_to_process:
            if len(songs) >= count:
                break
            try:
                self._set_status(
                    t("ai-radio-candidates-matching", title=suggestion.title)
                )
                song = await matcher.match(suggestion)
            except Exception:  # noqa
                logger.exception(
                    "AI radio failed to match song suggestion: %s", suggestion
                )
                continue
            if song is None:
                continue
            if self._is_duplicate(song, songs):
                continue
            self._seen_songs.add(song)
            songs.append(song)
        return songs

    def normalize_fetch_count(self, number: int):
        return max(1, min(number, self._candidate_batch_size))

    def _is_duplicate(self, song, batch) -> bool:
        return (
            song in self._seen_songs
            or song in batch
            or song in self._app.playlist.list()
        )

    def _create_matcher(self):
        if self._matcher_cls is None:
            return SongSuggestionMatcher(self._app)
        return self._matcher_cls(self._app)


class AIRadioFMAdapter:
    """Connect AI radio sessions to FM mode."""

    def __init__(
        self,
        app: "App",
        normalize_fetch_count,
        fetch_more_songs,
        on_finished,
    ):
        self._app = app
        self._normalize_fetch_count = normalize_fetch_count
        self._fetch_more_songs = fetch_more_songs
        self._on_finished = on_finished
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active and self._app.playlist.mode is PlaylistMode.fm

    def activate(self, reset=True):
        if self._app.fm.is_active:
            self._app.fm.deactivate()

        self._active = True
        self._app.playlist.mode_changed.connect(self._on_playlist_mode_changed)
        self._app.fm.activate(self.fetch_songs, reset=reset)

    def deactivate(self):
        if self.is_active:
            self._app.fm.deactivate()
        else:
            self.finish()

    def finish(self):
        if self._active:
            self._app.playlist.mode_changed.disconnect(
                self._on_playlist_mode_changed
            )
        self._active = False

    async def fetch_songs(self, number: int):
        number = self._normalize_fetch_count(number)
        return await self._fetch_more_songs(number)

    def _on_playlist_mode_changed(self, mode):
        if mode is not PlaylistMode.fm:
            self._on_finished()


class AIRadioSession:
    """AI radio session backed by the existing FM queue."""

    def __init__(
        self,
        app: "App",
        matcher_cls=None,
        recommendation_agent_factory=None,
        candidate_batch_size=DEFAULT_CANDIDATE_BATCH_SIZE,
    ):
        self._app = app
        self.status = ""
        self.status_changed = Signal()
        self._recommender = AIRadioRecommender(
            app,
            self._set_status,
            matcher_cls=matcher_cls,
            recommendation_agent_factory=recommendation_agent_factory,
            candidate_batch_size=candidate_batch_size,
        )
        self._fm = AIRadioFMAdapter(
            app,
            normalize_fetch_count=self._recommender.normalize_fetch_count,
            fetch_more_songs=self._fetch_more_songs,
            on_finished=self._finish,
        )

    @property
    def is_active(self) -> bool:
        return self._fm.is_active

    @property
    def candidate_batch_size(self) -> int:
        return self._recommender.candidate_batch_size

    @property
    def preferences(self) -> list[str]:
        return self._recommender.preferences

    @property
    def avoidances(self) -> list[str]:
        return self._recommender.avoidances

    @property
    def preference_notes(self) -> list[str]:
        return self._recommender.preference_notes

    def activate(self, reset=True):
        old_session = self._app.ai.radio
        if old_session is not None and old_session is not self:
            old_session._finish()

        self._app.ai.radio = self
        self._fm.activate(reset=reset)

    def deactivate(self):
        self._fm.deactivate()

    @property
    def fetch_songs_func(self):
        return self._fm.fetch_songs

    def get_state_for_ai(self):
        return AIRadioState(
            active=self.is_active,
            current_song=self._app.playlist.current_song,
            candidates=self.list_upcoming_candidates(),
            candidate_batch_size=self.candidate_batch_size,
            preferences=self.preferences,
            avoidances=self.avoidances,
            preference_notes=self.preference_notes,
        ).to_ai_dict()

    def list_upcoming_candidates(self):
        return self._app.fm.candidates.list_candidates()

    def set_candidate_status(self, status: str):
        self._set_status(status)

    async def match_suggestions(
        self, suggestions: list["SongSuggestion"], count: int | None = None
    ):
        return await self._recommender.match_suggestions(suggestions, count=count)

    def update_preferences(
        self,
        preferences: list[str] | None = None,
        avoidances: list[str] | None = None,
        reason: str = "",
    ):
        return self._recommender.update_preferences(
            preferences=preferences,
            avoidances=avoidances,
            reason=reason,
        )

    async def recommend_song_suggestions(
        self, count: int, instructions: list[str] | None = None
    ) -> list[SongSuggestion]:
        """Recommend songs for AI radio without matching provider resources."""
        radio_state = {
            "preferences": instructions or [],
            "avoidances": [],
            "preference_notes": [],
        }
        return await self._recommender.recommend_suggestions(
            count, radio_state=radio_state
        )

    async def a_fetch_songs_func(self, number: int):
        return await self.fetch_songs_func(number)

    async def _fetch_more_songs(self, number: int):
        return await self._recommender.recommend_matched_songs(
            number,
            radio_state=self.get_state_for_ai(),
        )

    def _finish(self):
        self._fm.finish()
        self._set_status("")
        if self._app.ai.radio is self:
            self._app.ai.radio = None

    def _set_status(self, status: str):
        self.status = status
        self.status_changed.emit(status)


def _clean_texts(texts: list[str]) -> list[str]:
    return [text.strip() for text in texts if text.strip()]


def _normalize_positions(positions: list[int], candidate_count: int) -> list[int]:
    normalized = []
    for position in positions:
        if 1 <= position <= candidate_count and position not in normalized:
            normalized.append(position)
    return normalized
