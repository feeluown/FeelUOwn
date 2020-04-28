import warnings

from .base import BaseModel, ModelType


class PlaylistModel(BaseModel):
    class Meta:
        model_type = ModelType.playlist.value
        fields = ['name', 'cover', 'songs', 'desc']
        fields_display = ['name']
        allow_create_songs_g = False

    def __str__(self):
        return 'fuo://{}/playlists/{}'.format(self.source, self.identifier)

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if name == 'songs':
            warnings.warn('please use/implement .create_songs_g')
        return value

    def add(self, song_id):
        """add song to playlist, return true if succeed.

        If the song was in playlist already, return true.
        """
        pass

    def remove(self, song_id):
        """remove songs from playlist, return true if succeed

        If song is not in playlist, return true.
        """
        pass

    def create_songs_g(self):
        pass
