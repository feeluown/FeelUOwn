from feeluown.library import SongModel, BriefAlbumModel, BriefArtistModel, BriefSongModel


def test_cast_old_model_to_new_model(song):
    brief_song = BriefSongModel.from_orm(song)
    assert brief_song.title == 'hello world'


def test_song_model():
    identifier = '1'
    brief_album = BriefAlbumModel(identifier='1', name='Film', artists_name='Audrey')
    brief_artist = BriefArtistModel(identifier='1', name='Audrey')
    # song should be created
    song = SongModel(identifier=identifier, title='Moon', album=brief_album,
                     artists=[brief_artist], duration=240000)
    # check song's attribute value
    assert song.artists_name == 'Audrey'
