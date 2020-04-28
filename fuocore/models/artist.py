import warnings

from .base import BaseModel, ModelType


class ArtistModel(BaseModel):
    """Artist Model"""

    class Meta:
        model_type = ModelType.artist.value
        fields = ['name', 'cover', 'songs', 'desc', 'albums']
        fields_display = ['name']
        allow_create_songs_g = False
        allow_create_albums_g = False

    def __str__(self):
        return 'fuo://{}/artists/{}'.format(self.source, self.identifier)

    def create_songs_g(self):
        """create songs generator(alpha)"""
        pass

    def create_albums_g(self):
        pass

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if name == 'songs':
            warnings.warn('please use/implement .create_songs_g')
        return value
