from typing import TYPE_CHECKING

from feeluown.player.playlist import PlaylistMode

if TYPE_CHECKING:
    from feeluown.app import App
    from feeluown.library import BriefSongModel


class FMCandidateManager:
    """Manage upcoming FM candidates stored in the playlist."""

    def __init__(self, app: "App"):
        self._app = app

    @property
    def _playlist(self):
        return self._app.playlist

    def list_candidates(self) -> list["BriefSongModel"]:
        return self._playlist.list_fm_candidates()

    def remove(self, positions: list[int]) -> bool:
        if not self._is_active:
            return False
        candidates = self.list_candidates()
        remove_positions = _normalize_positions(positions, len(candidates))
        removed_songs = [candidates[position - 1] for position in remove_positions]
        for song in removed_songs:
            self._playlist.remove(song)
        return True

    def append(self, songs: list["BriefSongModel"]) -> bool:
        if not self._is_active:
            return False
        for song in songs:
            if song in self._playlist.list():
                continue
            self._playlist.fm_add(song)
        return True

    @property
    def _is_active(self):
        return self._playlist.mode is PlaylistMode.fm


def _normalize_positions(positions: list[int], candidate_count: int) -> list[int]:
    normalized = []
    for position in positions:
        if 1 <= position <= candidate_count and position not in normalized:
            normalized.append(position)
    return normalized
