from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt

from feeluown.gui.components.nowplaying import NowplayingCommentListView
from feeluown.library import BriefSongModel, BriefUserModel, CommentModel


class _Provider:
    def __init__(self, source, comments_by_song):
        self.identifier = source
        self.name = source.upper()
        self._comments_by_song = comments_by_song

    def song_list_hot_comments(self, song):
        return self._comments_by_song[song.identifier]


class _Library:
    def __init__(self, providers):
        self._providers = providers

    def get(self, source):
        return self._providers[source]

    def list(self):
        return list(self._providers.values())


def _comment(source, content):
    user = BriefUserModel(identifier=f"{source}-user", source=source, name="user")
    return CommentModel(
        identifier=f"{source}-comment",
        source=source,
        user=user,
        liked_count=1,
        content=content,
        time=0,
    )


@pytest.mark.asyncio
async def test_nowplaying_comments_can_switch_back_to_current_source(
    qtbot, app_mock
):
    current_song = BriefSongModel(
        identifier="current-song",
        source="current",
        title="Song",
        artists_name="Artist",
    )
    standby_song = BriefSongModel(
        identifier="standby-song",
        source="standby",
        title="Song",
        artists_name="Artist",
    )
    providers = {
        "current": _Provider("current", {"current-song": [_comment("current", "A")]}),
        "standby": _Provider("standby", {"standby-song": [_comment("standby", "B")]}),
    }

    app_mock.library = _Library(providers)
    app_mock.playlist.song_changed = SimpleNamespace(connect=lambda *_, **__: None)
    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)

    view._comment_standby_manager.reset(current_song)
    view._comment_standby_manager.add_standby_songs([standby_song])
    view._update_comment_source_selector()

    await view._on_comment_source_changed(1)
    model = view._comment_list.model()
    comment = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    assert comment.content == "B"

    await view._on_comment_source_changed(0)
    model = view._comment_list.model()
    comment = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    assert comment.content == "A"


@pytest.mark.asyncio
async def test_nowplaying_comments_selector_shows_and_switches_standby_songs(
    qtbot, app_mock
):
    current_song = BriefSongModel(
        identifier="current-song",
        source="current",
        title="Song",
        artists_name="Artist",
    )
    standby_song_1 = BriefSongModel(
        identifier="standby-song-1",
        source="standby",
        title="Song",
        artists_name="Artist 1",
    )
    standby_song_2 = BriefSongModel(
        identifier="standby-song-2",
        source="standby",
        title="Song",
        artists_name="Artist 2",
    )
    providers = {
        "current": _Provider("current", {"current-song": [_comment("current", "A")]}),
        "standby": _Provider(
            "standby",
            {
                "standby-song-1": [_comment("standby", "B")],
                "standby-song-2": [_comment("standby", "C")],
            },
        ),
    }

    app_mock.library = _Library(providers)
    app_mock.playlist.song_changed = SimpleNamespace(connect=lambda *_, **__: None)
    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)

    view._comment_standby_manager.reset(current_song)
    view._comment_standby_manager.add_standby_songs([standby_song_1, standby_song_2])
    view._update_comment_source_selector()

    assert view._comment_source_selector.itemText(1) == "STANDBY · Song - Artist 1"
    assert view._comment_source_selector.itemText(2) == "STANDBY · Song - Artist 2"

    await view._on_comment_source_changed(2)
    model = view._comment_list.model()
    comment = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    assert comment.content == "C"
