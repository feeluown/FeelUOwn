import pytest

from fuocore.cmds.show import router
from fuocore.provider import dummy_provider, Dummy, \
    DummyAlbumModel, DummyArtistModel, DummyPlaylistModel, \
    DummySongModel


@pytest.fixture
def ctx(library):
    library.register(dummy_provider)
    return {'library': library}


@pytest.fixture
def handle(ctx):
    return lambda path: router.dispatch(path, ctx)


def test_cmd_show_model(handle):
    song = handle(f'/{Dummy}/songs/{Dummy}')
    assert song.identifier == Dummy


def test_cmd_show_lyric(handle):
    lyric = handle(f'/{Dummy}/songs/{Dummy}/lyric')
    assert not lyric


def test_cmd_show_artist_albums(mocker, handle):
    artist = DummyArtistModel.get(Dummy)
    album = DummyAlbumModel.get(Dummy)
    artist.albums = [album]
    mocker.patch.object(DummyArtistModel, 'get', return_value=artist)

    albums = handle(f'/{Dummy}/artists/{Dummy}/albums')
    assert len(albums) == 1 and albums[0] == album


def test_cmd_show_playlist_songs(mocker, handle):
    playlist = DummyPlaylistModel.get(Dummy)
    song = DummySongModel.get(Dummy)
    playlist.songs = [song]
    mocker.patch.object(DummyPlaylistModel, 'get', return_value=playlist)

    songs = handle(f'/{Dummy}/playlists/{Dummy}/songs')
    assert len(songs) == 1 and songs[0] == song
