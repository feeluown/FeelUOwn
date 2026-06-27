import logging
from collections import deque
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Iterable, Optional

from feeluown.i18n import t
from feeluown.player.playlist import PlaylistMode
from feeluown.utils.dispatch import Signal

if TYPE_CHECKING:
    from feeluown.app import App
    from feeluown.library import BriefSongModel


logger = logging.getLogger(__name__)


DEFAULT_CANDIDATE_BATCH_SIZE = 3


@dataclass
class AIRadioCandidateUpdateResult:
    kept_count: int
    removed_count: int
    requested_count: int
    added_songs: list["BriefSongModel"]


@dataclass
class AIRadioCandidateUpdatePlan:
    keep_count: int
    fetch_count: int


class AIRadioSession:
    """AI radio session backed by the existing FM queue.

    The session stores user instructions from the shared AI chat and exposes an
    async fetch_songs_func for FM. Matched songs are still added to the playlist
    by FM, making playlist the canonical candidate/upcoming-song view.
    """

    def __init__(
        self,
        app: "App",
        initial_songs: Optional[Iterable["BriefSongModel"]] = None,
        matcher_cls=None,
        candidate_batch_size=DEFAULT_CANDIDATE_BATCH_SIZE,
    ):
        self._app = app
        self._pending_songs = deque(initial_songs or [])
        self._matcher_cls = matcher_cls
        self._candidate_batch_size = candidate_batch_size
        self._instructions = []
        self._seen_songs = set()
        self._active = False
        self.status = ""
        self.status_changed = Signal()

    @property
    def is_active(self) -> bool:
        return self._active and self._app.playlist.mode is PlaylistMode.fm

    @property
    def instructions(self) -> list[str]:
        return list(self._instructions)

    def activate(self, reset=True):
        old_session = self._app.ai.radio
        if old_session is not None and old_session is not self:
            old_session._finish()

        if self._app.fm.is_active:
            self._app.fm.deactivate()

        self._app.ai.radio = self
        self._active = True
        self._app.playlist.mode_changed.connect(self._on_playlist_mode_changed)
        self._app.fm.activate(self.a_fetch_songs_func, reset=reset)

    def deactivate(self):
        if self.is_active:
            self._app.fm.deactivate()
        else:
            self._finish()

    def add_instruction(self, text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        self._instructions.append(text)
        return True

    async def update_candidates(self, instruction: str, count: int | None = None):
        if not self.add_instruction(instruction):
            return AIRadioCandidateUpdateResult(0, 0, 0, [])

        count = count or self._candidate_batch_size
        count = max(1, min(count, self._candidate_batch_size))
        current_candidates = self.list_upcoming_candidates()
        plan = self._create_update_plan(instruction, count, len(current_candidates))

        self._set_status(t("ai-radio-candidates-clearing"))
        removed_songs = self.trim_upcoming_candidates(plan.keep_count)
        self._pending_songs.clear()
        if plan.fetch_count <= 0:
            if removed_songs:
                self._set_status(t("ai-radio-candidates-cleared"))
            else:
                self._set_status(t("ai-radio-candidates-kept"))
            return AIRadioCandidateUpdateResult(
                plan.keep_count,
                len(removed_songs),
                0,
                [],
            )

        songs = await self.a_fetch_songs_func(plan.fetch_count)
        if songs:
            self._set_status(t("ai-radio-candidates-adding", count=len(songs)))
            for song in songs:
                self._app.playlist.fm_add(song)
            self._set_status(t("ai-radio-candidates-updated", count=len(songs)))
        else:
            self._set_status(t("ai-radio-candidates-update-failed"))
        return AIRadioCandidateUpdateResult(
            plan.keep_count,
            len(removed_songs),
            plan.fetch_count,
            songs,
        )

    def list_upcoming_candidates(self):
        songs = list(self._app.playlist.list())
        current_song = self._app.playlist.current_song
        if current_song is None or current_song not in songs:
            return songs
        return songs[songs.index(current_song) + 1:]

    def trim_upcoming_candidates(self, keep_count=0):
        songs = self.list_upcoming_candidates()
        keep_count = max(0, min(keep_count, len(songs)))
        removed_songs = songs[keep_count:]
        for song in removed_songs:
            self._app.playlist.remove(song)
        return removed_songs

    async def a_fetch_songs_func(self, number: int):
        number = max(1, min(number, self._candidate_batch_size))
        songs = self._take_pending_songs(number)
        if len(songs) >= number:
            return songs

        if self._app.ai is None:
            logger.warning("AI radio cannot fetch songs because AI is unavailable")
            return songs

        try:
            copilot = self._app.ai.get_copilot()
            self._set_status(
                t("ai-radio-candidates-requesting", count=number - len(songs))
            )
            suggestions = await copilot.recommend_songs(
                number - len(songs),
                instructions=self.instructions,
            )
        except Exception:  # noqa
            logger.exception("AI radio failed to recommend songs")
            return songs

        matcher = self._create_matcher()
        for suggestion in suggestions:
            if len(songs) >= number:
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

    def _take_pending_songs(self, number: int):
        songs = []
        while self._pending_songs and len(songs) < number:
            song = self._pending_songs.popleft()
            if self._is_duplicate(song, songs):
                continue
            self._seen_songs.add(song)
            songs.append(song)
        return songs

    def _is_duplicate(self, song, batch) -> bool:
        return (
            song in self._seen_songs
            or song in batch
            or song in self._app.playlist.list()
        )

    def _create_matcher(self):
        if self._matcher_cls is None:
            from feeluown.ai import SongSuggestionMatcher

            return SongSuggestionMatcher(self._app)
        return self._matcher_cls(self._app)

    def _on_playlist_mode_changed(self, mode):
        if mode is not PlaylistMode.fm:
            self._finish()

    def _finish(self):
        if self._active:
            self._app.playlist.mode_changed.disconnect(self._on_playlist_mode_changed)
        self._active = False
        self._set_status("")
        if self._app.ai.radio is self:
            self._app.ai.radio = None

    def _set_status(self, status: str):
        self.status = status
        self.status_changed.emit(status)

    def _create_update_plan(
        self, instruction: str, count: int, candidate_count: int
    ) -> AIRadioCandidateUpdatePlan:
        keep_count = self._parse_keep_count(instruction, candidate_count)
        if self._is_clear_only_instruction(instruction):
            return AIRadioCandidateUpdatePlan(0, 0)
        if self._is_keep_all_instruction(instruction):
            return AIRadioCandidateUpdatePlan(keep_count, 0)
        fetch_count = max(0, count - keep_count)
        return AIRadioCandidateUpdatePlan(keep_count, fetch_count)

    def _parse_keep_count(self, instruction: str, candidate_count: int) -> int:
        normalized = instruction.strip().lower()
        if not normalized:
            return 0
        if any(token in normalized for token in ("保留全部", "全部保留", "keep all")):
            return candidate_count
        if any(token in normalized for token in ("满意", "可以了", "不用改")):
            return candidate_count

        match = re.search(
            r"(?:保留|keep)\s*(?:前|first)?\s*([0-9]+|一|二|两|三)\s*(?:首|个|songs?)?",
            normalized,
        )
        if match is None:
            return 0
        value = self._parse_count(match.group(1))
        return max(0, min(value, candidate_count))

    def _parse_count(self, text: str) -> int:
        chinese_numbers = {"一": 1, "二": 2, "两": 2, "三": 3}
        if text in chinese_numbers:
            return chinese_numbers[text]
        return int(text)

    def _is_clear_only_instruction(self, instruction: str) -> bool:
        normalized = instruction.strip().lower()
        if not any(token in normalized for token in ("清空", "清除", "clear")):
            return False
        refill_tokens = ("换", "重新", "推荐", "补", "再", "replace", "recommend")
        return not any(token in normalized for token in refill_tokens)

    def _is_keep_all_instruction(self, instruction: str) -> bool:
        normalized = instruction.strip().lower()
        keep_all_tokens = ("保留全部", "全部保留", "keep all")
        satisfied_tokens = ("满意", "可以了", "不用改")
        return any(
            token in normalized for token in keep_all_tokens + satisfied_tokens
        )
