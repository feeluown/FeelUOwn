from .base import BaseModel, ModelType


class UserModel(BaseModel):
    """User Model

    :param name: user name
    :param playlists: playlists created by user
    :param fav_playlists: playlists collected by user
    :param fav_songs: songs collected by user
    :param fav_albums: albums collected by user
    :param fav_artists: artists collected by user
    """
    class Meta:
        allow_fav_songs_add = False
        allow_fav_songs_remove = False
        allow_fav_playlists_add = False
        allow_fav_playlists_remove = False
        allow_fav_albums_add = False
        allow_fav_albums_remove = False
        allow_fav_artists_add = False
        allow_fav_artists_remove = False

        model_type = ModelType.user.value
        fields = ['name', 'playlists', 'fav_playlists', 'fav_songs',
                  'fav_albums', 'fav_artists', 'rec_songs', 'rec_playlists']
        fields_display = ['name']

    def add_to_fav_songs(self, song_id):
        """add song to favorite songs, return True if success

        :param song_id: song identifier
        :return: Ture if success else False
        :rtype: boolean
        """
        pass

    def remove_from_fav_songs(self, song_id):
        pass

    def add_to_fav_playlists(self, playlist_id):
        pass

    def remove_from_fav_playlists(self, playlist_id):
        pass

    def add_to_fav_albums(self, album_id):
        pass

    def remove_from_fav_albums(self, album_id):
        pass

    def add_to_fav_artists(self, aritst_id):
        pass

    def remove_from_fav_artists(self, artist_id):
        pass
