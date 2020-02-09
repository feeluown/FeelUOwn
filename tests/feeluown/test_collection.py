from fuocore.models.uri import ResolveFailed, ResolverNotFound
from feeluown.collection import Collection


def test_collection_load(tmp_path, song, mocker):
    mock_resolve = mocker.patch('feeluown.collection.resolve',
                                return_value=song)
    path = tmp_path / 'test.fuo'
    path.touch()
    text = 'fuo://fake/songs/1  # hello - Tom'
    path.write_text(text)
    coll = Collection(str(path))
    coll.load()
    mock_resolve.called_once_with(text)
    assert coll.models[0] is song


def test_collection_load_invalid_file(tmp_path, mocker):
    mocker.patch('feeluown.collection.resolve',
                 side_effect=ResolveFailed)
    path = tmp_path / 'test.fuo'
    path.touch()
    path.write_text('...')
    coll = Collection(str(path))
    coll.load()
    assert len(coll.models) == 0

    mocker.patch('feeluown.collection.resolve',
                 side_effect=ResolverNotFound)
    coll.load()
    assert len(coll.models) == 0


def test_collection_add(album, artist, song, tmp_path):
    directory = tmp_path / 'sub'
    directory.mkdir()
    f = directory / 'test.fuo'
    f.touch()
    coll = Collection(str(f))

    # test add album
    coll.add(album)
    expected = 'fuo://fake/albums/0\t# blue and green - \n'
    text = f.read_text()
    assert text == expected

    # test add artist
    coll.add(artist)
    expected = 'fuo://fake/artists/0\t# mary\n' + expected
    text = f.read_text()
    assert text == expected

    # test add song
    coll.add(song)
    text = f.read_text()
    expected = ('fuo://fake/songs/0\t# hello world'
                ' - mary - blue and green - 10:00\n') + expected
    assert text == expected


def test_collection_add_song_to_sys_album(song, tmp_path):
    f = tmp_path / 'Albums.fuo'
    f.touch()
    coll = Collection(str(f))
    coll.load()
    assert coll.add(song) is False
