from types import SimpleNamespace

import pytest

from feeluown.ai import SongSuggestion
from feeluown.ai.matcher import SongSuggestionMatcher
from feeluown.library import BriefSongModel, Library, Provider, SimpleSearchResult


class SearchProvider(Provider):
    def __init__(self, identifier, songs):
        self._identifier = identifier
        self._songs = songs
        self.search_calls = []

    @property
    def identifier(self):
        return self._identifier

    @property
    def name(self):
        return self._identifier

    def search(self, keyword, **kwargs):
        self.search_calls.append((keyword, kwargs))
        return SimpleSearchResult(q=keyword, songs=self._songs)


def create_song(identifier, source, title="Song", artists_name="Artist"):
    return BriefSongModel(
        identifier=identifier,
        source=source,
        title=title,
        artists_name=artists_name,
    )


def create_matcher_app(library):
    return SimpleNamespace(library=library)


@pytest.mark.asyncio
async def test_matcher_prefers_configured_standby_provider():
    library = Library(providers_standby=["standby"])
    normal = SearchProvider("normal", [create_song("normal-song", "normal")])
    standby = SearchProvider("standby", [create_song("standby-song", "standby")])
    library.register(normal)
    library.register(standby)
    matcher = SongSuggestionMatcher(create_matcher_app(library))

    song = await matcher.match(
        SongSuggestion(title="Song", artists_name="Artist", description="")
    )

    assert song.identifier == "standby-song"
    assert standby.search_calls
    assert normal.search_calls == []


@pytest.mark.asyncio
async def test_matcher_falls_back_when_standby_provider_has_no_match():
    library = Library(providers_standby=["standby"])
    normal = SearchProvider("normal", [create_song("normal-song", "normal")])
    standby = SearchProvider(
        "standby",
        [create_song("standby-mismatch", "standby", title="Other")],
    )
    library.register(normal)
    library.register(standby)
    matcher = SongSuggestionMatcher(create_matcher_app(library))

    song = await matcher.match(
        SongSuggestion(title="Song", artists_name="Artist", description="")
    )

    assert song.identifier == "normal-song"
    assert standby.search_calls
    assert normal.search_calls
