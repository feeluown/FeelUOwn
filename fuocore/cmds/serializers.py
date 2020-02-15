"""

**brief**

line, subset of fields_display::

    fuo://local/songs/1  # title - artists - album

json, only display fields::

    {...}


**detail**

display, show all fields::

    identifier:   1
      provider:   local
         title:   title
         album:   fuo://lcaol/album  # name
      artists::
                  fuo://local/artists/1  # name
                  fuo://local/artists/2  # name

json, show all fields::

    {...}
"""

from fuocore.models import BaseModel, SongModel, ArtistModel, AlbumModel, \
    PlaylistModel, UserModel


SONG = 'song'
ARTIST = 'artist'
ALBUM = 'album'
USER = 'user'
PLAYLIST = 'playlist'


class AbstractSerializer:
    def serialize(self, obj):
        pass


class SequenceSerializer:
    """list/tuple serializer

    string/bytes is not in consideration
    """

    def serialize(self, obj):
        if len(obj) > 0 and isinstance(obj[0], BaseModel):
            serializer_cls = ModelBaseSerializer.get_serializer_cls(obj[0])
            serializer = serializer_cls(brief=True, fetch=False)
            value = [serializer.serialize(item) for item in obj]
        else:
            value = obj
        return value


class ModelBaseSerializer(AbstractSerializer):
    _mapping = {}  # model serializer mapping

    def __init__(self, brief=True, fetch=None, **kwargs):
        self._brief = brief
        self._fetch = fetch or not brief

    def serialize(self, model):
        json_ = {"provider": model.source,
                 "type": self._type,
                 "identifier": model.identifier,
                 "uri": str(model)}

        if self._brief:
            fields = model.meta.fields_display
        else:
            fields = self._declared_fields
        for field in fields:
            obj = getattr(model, field if self._fetch else field + "_display")
            if isinstance(obj, BaseModel):
                serializer_cls = self.get_serializer_cls(obj)
                serializer = serializer_cls(brief=True, fetch=False)
                value = serializer.serialize(obj)
            elif isinstance(obj, (list, tuple)):
                serializer = SequenceSerializer()
                value = serializer.serialize(obj)
            else:
                value = obj
            json_[field] = value
        return json_

    @classmethod
    def get_serializer_cls(cls, obj):
        for model_cls, serializer_cls in cls._mapping.items():
            if isinstance(obj, model_cls):
                return serializer_cls
        return None


class ModelSerializerMeta(type):
    def __new__(cls, name, bases, attrs):
        Meta = attrs.pop('Meta', None)
        klass = type.__new__(cls, name, bases, attrs)
        if Meta:  # we assume
            fields = getattr(Meta, 'fields', [])
            ModelBaseSerializer._mapping[Meta.model] = klass
            klass._declared_fields = fields
            klass._type = Meta.type_
        return klass


class SongSerializer(ModelBaseSerializer, metaclass=ModelSerializerMeta):
    class Meta:
        type_ = SONG
        model = SongModel
        fields = ('title', 'duration', 'url', 'artists', 'album')


class ArtistSerializer(ModelBaseSerializer, metaclass=ModelSerializerMeta):
    class Meta:
        type_ = ARTIST
        model = ArtistModel
        fields = ('name', 'songs')


class AlbumSerializer(ModelBaseSerializer, metaclass=ModelSerializerMeta):
    class Meta:
        type_ = ALBUM
        model = AlbumModel
        fields = ('name', 'artists', 'songs')


class PlaylistSerializer(ModelBaseSerializer, metaclass=ModelSerializerMeta):
    class Meta:
        type_ = PLAYLIST
        model = PlaylistModel
        fields = ('name', )


class UserSerializer(ModelBaseSerializer, metaclass=ModelSerializerMeta):
    class Meta:
        type_ = USER
        model = UserModel
        fields = ('name', 'playlists')
