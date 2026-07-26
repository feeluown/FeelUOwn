from unittest.mock import MagicMock, call

from feeluown.ai.model_cache import ModelCache
from feeluown.library import BriefSongModel, ModelType


def test_model_cache_normalizes_uri_before_lookup():
    song = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Song",
    )
    library = MagicMock()
    cache = ModelCache(library)
    cache.set_model(song)

    resolved = cache.get(
        "fuo://fake/songs/song-1  # Song - Singer"
    )

    assert resolved is song
    library.model_get.assert_not_called()


def test_model_cache_applies_capacity_to_registered_and_fetched_models():
    registered_song = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Registered Song",
    )
    fetched_song_1 = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Fetched Song 1",
    )
    fetched_song_2 = BriefSongModel(
        source="fake",
        identifier="song-2",
        title="Fetched Song 2",
    )
    library = MagicMock()
    library.model_get.side_effect = [fetched_song_2, fetched_song_1]
    cache = ModelCache(library, maxsize=1)
    cache.set_model(registered_song)

    assert cache.get("fuo://fake/songs/song-1") is registered_song
    assert cache.get("fuo://fake/songs/song-2") is fetched_song_2
    assert cache.get("fuo://fake/songs/song-1") is fetched_song_1
    assert library.model_get.call_args_list == [
        call("fake", ModelType.song, "song-2"),
        call("fake", ModelType.song, "song-1"),
    ]
