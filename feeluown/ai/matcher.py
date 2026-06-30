from feeluown.app import App
from feeluown.library import BriefSongModel, SongStandbyOptions


class SongSuggestionMatcher:
    def __init__(self, app: App):
        self._app = app

    async def match(self, suggestion) -> BriefSongModel | None:
        """Match a suggested song by title and artists name.

        This API is in alpha stage.
        """
        origin = suggestion.to_brief_song()
        standbys = await self._app.library.a_list_song_standby_v3(
            origin,
            SongStandbyOptions(single_full_score_per_source=True),
        )
        return standbys[0] if standbys else None
