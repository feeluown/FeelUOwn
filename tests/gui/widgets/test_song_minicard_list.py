import pytest
from PyQt6.QtCore import QModelIndex, Qt

from feeluown.utils import aio
from feeluown.player import Playlist
from feeluown.gui.components.player_playlist import PlayerPlaylistModel


@pytest.mark.asyncio
async def test_player_playlist_model_removes_cached_image(app_mock, qtbot, song):
    async def fetch_cover(_, cb): cb(b"image content")

    playlist = Playlist(app_mock)
    model = PlayerPlaylistModel(playlist, fetch_cover)

    assert model.rowCount() == 0
    playlist.add(song)
    assert model.rowCount() == 1

    model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
    await aio.sleep(0.1)
    assert len(model.image_cache) == 1

    playlist.remove(song)
    assert len(model.image_cache) == 0


def test_player_playlist_model_mirrors_existing_playlist(app_mock, song, song1):
    playlist = Playlist(app_mock, songs=[song, song1])
    model = PlayerPlaylistModel(playlist, lambda *_: None)

    assert model.rowCount() == 2
    assert not model.canFetchMore(QModelIndex())


def test_player_playlist_model_clear_with_partial_cache_does_not_crash(
    app_mock, song, song1
):
    playlist = Playlist(app_mock, songs=[song, song1])
    model = PlayerPlaylistModel(playlist, lambda *_: None)
    model._items = [song]

    playlist.clear()

    assert model.rowCount() == 0


def test_player_playlist_model_ignores_empty_add_signal(app_mock, song):
    playlist = Playlist(app_mock, songs=[song])
    model = PlayerPlaylistModel(playlist, lambda *_: None)

    playlist.batch_add([song])

    assert model.rowCount() == 1
