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

    view._platform_selector.addItem("CURRENT", "current")
    view._platform_selector.addItem("STANDBY", "standby")
    view._source_state.reset(current_song)
    view._source_state.set_standby_map({"standby": standby_song})

    await view._on_platform_changed(1)
    model = view._comment_list.model()
    comment = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    assert comment.content == "B"

    await view._on_platform_changed(0)
    model = view._comment_list.model()
    comment = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    assert comment.content == "A"
