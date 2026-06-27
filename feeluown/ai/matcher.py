from feeluown.app import App
from feeluown.library import (
    BriefSongModel,
    get_standby_score,
    STANDBY_FULL_SCORE,
    STANDBY_DEFAULT_MIN_SCORE,
)


class SongSuggestionMatcher:
    def __init__(self, app: App):
        self._app = app

    async def match(self, suggestion) -> BriefSongModel | None:
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
