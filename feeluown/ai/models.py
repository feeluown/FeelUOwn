from dataclasses import dataclass

from feeluown.library import BriefSongModel, ModelState


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
