from feeluown.library import ResolveFailed, ResolverNotFound, reverse
from feeluown.collection import Collection, CollectionManager, LIBRARY_FILENAME, \
    POOL_FILENAME


def test_collection_load(tmp_path, song, mocker):
    mock_resolve = mocker.patch('feeluown.collection.resolve',
                                return_value=song)
    path = tmp_path / 'test.fuo'
    path.touch()
    text = 'fuo://fake/songs/1  # hello - Tom'
    path.write_text(text)
    coll = Collection(str(path))
    coll.load()
    mock_resolve.assert_called_once_with(text)
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


def test_collection_add_and_remove(album, artist, song, tmp_path):
    directory = tmp_path / 'sub'
    directory.mkdir()
    f = directory / 'test.fuo'
    f.touch()
    coll = Collection(str(f))

    # test add album
    coll.add(album)
    expected = 'fuo://fake/albums/0\t# blue and green\n'
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

    # test remove song
    coll.remove(song)
    assert reverse(song) not in f.read_text()
    assert song not in coll.models


def test_load_and_write_file_with_metadata(song, tmp_path, mocker):
    mocker.patch('feeluown.collection.resolve', return_value=song)
    f = tmp_path / 'test.fuo'
    f.touch()
    text = '''\
+++
title = 'title'
xx = 2
+++
fuo://fake/songs/0
'''
    f.write_text(text)
    coll = Collection(str(f))
    coll.load()

    # metadata should be correctly loaded
    assert coll.name == 'title'

    # field `updated` should be written into file
    coll.remove(song)
    line = f.read_text().split('\n')[3]
    assert line.startswith('updated')

    coll.add(song)
    text = f.read_text().strip()
    lines = text.split('\n')
    assert len(lines) == 6
    line = lines[-1]
    assert line.startswith('fuo://fake/songs/0')


def test_load_and_write_file_with_no_metadata(song, song3, tmp_path, mocker):
    mocker.patch('feeluown.collection.resolve', return_value=song)
    f = tmp_path / 'test.fuo'
    f.touch()
    first_line = 'fuo://fake/songs/0\n'  # song
    remain_lines = 'fuo://fake/songs/1\n' + 'fuo://fake/songs/2\n'
    text = first_line + remain_lines
    f.write_text(text)
    coll = Collection(str(f))
    coll.load()
    assert coll.name == 'test'  # name should be filename

    coll.remove(song)
    # 1. the first line should be removed
    # 2. no metadata should be written
    assert f.read_text() == remain_lines

    coll.add(song3)
    lines = f.read_text().split('\n')
    assert len(lines) == 4  # three plus two empty
    assert lines[0].startswith('fuo://fake/songs/3')


def test_coll_mgr_generate_library_coll(app_mock, tmp_path):
    coll_mgr = CollectionManager(app_mock)
    directory = tmp_path / 'sub'
    directory.mkdir()
    coll_mgr.default_dir = str(directory)

    # Simulate a fake Album.fuo file.
    album = 'fuo://fake/albums/0'
    f = directory / 'Albums.fuo'
    f.touch()
    f.write_text(f'{album}\n')

    # Check if the library collection file is generated.
    coll_mgr.generate_library_coll_if_needed([str(f)])
    library_coll_file = directory / 'library.fuo'
    assert library_coll_file.exists()

    # Check if the album is copied to library collection.
    with library_coll_file.open() as f:
        content = f.read()
    assert album in content


def test_collection_create_empty(tmp_path):
    path = tmp_path / 'test.fuo'
    Collection.create_empty(path, "Hello World")

    coll = Collection(path)
    coll.load()
    assert coll.models == []
    assert coll.name == 'Hello World'


def test_predefined_collection_should_on_top(tmp_path, app_mock, mocker):
    def new_collection(path):
        path.touch()
        coll = Collection(str(path))
        coll.load()
        return coll

    coll1 = new_collection(tmp_path / '1.fuo')
    coll2 = new_collection(tmp_path / '2.fuo')
    coll_library = new_collection(tmp_path / LIBRARY_FILENAME)
    coll_pool = new_collection(tmp_path / POOL_FILENAME)

    coll_mgr = CollectionManager(app_mock)
    mocker.patch.object(CollectionManager, '_scan',
                        return_value=[coll1, coll_library, coll_pool, coll2])
    coll_mgr.scan()
    assert list(coll_mgr.listall()) == [coll_library, coll_pool, coll1, coll2]
