from feeluown.collection import Collection


def test_collection_add(album, artist, song, tmp_path):
    direcotry = tmp_path / 'sub'
    direcotry.mkdir()
    f = direcotry / 'test.fuo'
    f.touch()
    coll = Collection(str(f))

    # test add album
    coll.add(album)
    expected = 'fuo://fake/albums/0\t#blue and green - \n'
    text = f.read_text()
    assert text == expected

    # test add artist
    coll.add(artist)
    expected = 'fuo://fake/artists/0\t#mary\n' + expected
    text = f.read_text()
    assert text == expected

    # test add song
    coll.add(song)
    text = f.read_text()
    expected = ('fuo://fake/songs/0\t#hello world'
                ' - mary - blue and green - 10:00\n') + expected
    assert text == expected
