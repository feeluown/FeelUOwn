import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# Mock feeluown.mpv before importing components that transitively import it.
_original_mpv_module = sys.modules.get('feeluown.mpv')
sys.modules['feeluown.mpv'] = MagicMock()

from PyQt6.QtCore import Qt

from feeluown.gui.components.nowplaying import NowplayingCommentListView
from feeluown.i18n import t
from feeluown.library import (
    BriefSongModel,
    BriefCommentModel,
    BriefUserModel,
    CommentModel,
    SupportsSongHotComments,
)


def teardown_module():
    if _original_mpv_module is not None:
        sys.modules['feeluown.mpv'] = _original_mpv_module
    else:
        sys.modules.pop('feeluown.mpv', None)


class DummyPlaylist:
    def __init__(self, song):
        self.current_song = song
        self.song_changed = SimpleNamespace(connect=MagicMock())


class DummyProvider(SupportsSongHotComments):
    def __init__(self, identifier="dummy", name="Dummy"):
        self.identifier = identifier
        self.name = name

    def song_list_hot_comments(self, song):
        return [
            CommentModel(
                identifier="c1",
                source=self.identifier,
                user=BriefUserModel(identifier="u1", source=self.identifier, name="user"),
                content=f"comment from {self.identifier}",
                liked_count=1,
                time=0,
            )
        ]


@pytest.fixture
def app_mock():
    app = MagicMock()
    return app


@pytest.mark.asyncio
async def test_refresh_loads_current_provider_comments(qtbot, app_mock):
    song = BriefSongModel(
        identifier="1", source="pvd_a", title="hello", artists_name="world"
    )
    app_mock.playlist = DummyPlaylist(song)
    app_mock.library.list.return_value = [
        DummyProvider("pvd_a", "Provider A"),
    ]
    app_mock.library.get.return_value = DummyProvider("pvd_a", "Provider A")
    app_mock.library.a_search_song_matches = AsyncMock(return_value=[])

    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)
    await view.refresh()

    model = view._list_view.model()
    assert model.rowCount() == 1
    comment = model.data(model.index(0), role=Qt.ItemDataRole.UserRole)
    assert comment.content == "comment from pvd_a"


@pytest.mark.asyncio
async def test_search_other_sources_populates_combo_box(qtbot, app_mock):
    song = BriefSongModel(
        identifier="1", source="pvd_a", title="hello", artists_name="world"
    )
    matched_song = BriefSongModel(
        identifier="2", source="pvd_b", title="hello", artists_name="world"
    )

    app_mock.playlist = DummyPlaylist(song)
    app_mock.library.list.return_value = [
        DummyProvider("pvd_a", "Provider A"),
        DummyProvider("pvd_b", "Provider B"),
    ]
    app_mock.library.get.side_effect = lambda pid: {
        "pvd_a": DummyProvider("pvd_a", "Provider A"),
        "pvd_b": DummyProvider("pvd_b", "Provider B"),
    }.get(pid)
    app_mock.library.a_search_song_matches = AsyncMock(return_value=[
        ("pvd_b", matched_song, 1.0),
    ])

    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)
    await view.refresh()

    assert view._source_combo.count() == 2
    assert view._source_combo.itemText(0) == t("track-comments-source-current")
    assert view._source_combo.itemData(0) == "pvd_a"
    assert view._source_combo.itemText(1) == "Provider B"
    assert view._source_combo.itemData(1) == "pvd_b"


@pytest.mark.asyncio
async def test_combo_box_change_fetches_other_comments(qtbot, app_mock):
    song = BriefSongModel(
        identifier="1", source="pvd_a", title="hello", artists_name="world"
    )
    matched_song = BriefSongModel(
        identifier="2", source="pvd_b", title="hello", artists_name="world"
    )

    app_mock.playlist = DummyPlaylist(song)
    app_mock.library.list.return_value = [
        DummyProvider("pvd_a", "Provider A"),
        DummyProvider("pvd_b", "Provider B"),
    ]
    app_mock.library.get.side_effect = lambda pid: {
        "pvd_a": DummyProvider("pvd_a", "Provider A"),
        "pvd_b": DummyProvider("pvd_b", "Provider B"),
    }.get(pid)
    app_mock.library.a_search_song_matches = AsyncMock(return_value=[
        ("pvd_b", matched_song, 1.0),
    ])

    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)
    await view.refresh()

    # Switch to Provider B manually to avoid triggering the signal handler.
    view._source_combo.blockSignals(True)
    view._source_combo.setCurrentIndex(1)
    view._source_combo.blockSignals(False)
    await view._on_source_changed(1)

    model = view._list_view.model()
    assert model.rowCount() == 1
    comment = model.data(model.index(0), role=Qt.ItemDataRole.UserRole)
    assert comment.content == "comment from pvd_b"


@pytest.mark.asyncio
async def test_search_skips_when_song_changed(qtbot, app_mock):
    song = BriefSongModel(
        identifier="1", source="pvd_a", title="hello", artists_name="world"
    )
    other_song = BriefSongModel(
        identifier="3", source="pvd_a", title="other", artists_name="world"
    )
    matched_song = BriefSongModel(
        identifier="2", source="pvd_b", title="hello", artists_name="world"
    )

    app_mock.playlist = DummyPlaylist(song)
    app_mock.library.list.return_value = [
        DummyProvider("pvd_a", "Provider A"),
        DummyProvider("pvd_b", "Provider B"),
    ]
    app_mock.library.get.side_effect = lambda pid: {
        "pvd_a": DummyProvider("pvd_a", "Provider A"),
        "pvd_b": DummyProvider("pvd_b", "Provider B"),
    }.get(pid)

    async def slow_search(_):
        # Simulate that the song changes while searching.
        app_mock.playlist.current_song = other_song
        return [("pvd_b", matched_song, 1.0)]

    app_mock.library.a_search_song_matches = slow_search

    view = NowplayingCommentListView(app_mock)
    qtbot.addWidget(view)
    await view.refresh()

    # The combo box should not have been populated because the song changed.
    assert view._source_combo.count() == 1
