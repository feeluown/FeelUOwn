from .base import Serializer, SerializerMeta, InvalidOptionsCombination
from .model_helpers import ModelSerializerMixin, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin


class JsonSerializer(Serializer):
    _mapping = {}


class ModelSerializer(JsonSerializer, ModelSerializerMixin):

    def __init__(self, **options):
        if options.get('brief') is False and options.get('fetch') is False:
            raise InvalidOptionsCombination(
                "fetch can't be False when brief is False")
        super().__init__(**options)
        if self.options['brief'] is False:
            self.options['fetch'] = True

    def serialize(self, model):
        json_ = {}
        for field, value in self._get_items(model):
            serializer_cls = self.get_serializer_cls(value)
            value_json = serializer_cls(brief=True, fetch=False).serialize(value)
            json_[field] = value_json
        return json_


class ListSerializer(JsonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (list, )

    def serialize(self, list_):
        if not list_:
            return []
        item0 = list_[0]
        serializer_cls = JsonSerializer.get_serializer_cls(item0)
        serializer = serializer_cls(brief=True, fetch=False)
        result = []
        for item in list_:
            result.append(serializer.serialize(item))
        return result


class SimpleTypePlainSerializer(JsonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float)

    def serialize(self, object):
        return object


class SongSerializer(ModelSerializer, SongSerializerMixin,
                     metaclass=SerializerMeta):
    pass


class ArtistSerializer(ModelSerializer, ArtistSerializerMixin,
                       metaclass=SerializerMeta):
    pass


class AlbumSerializer(ModelSerializer, AlbumSerializerMixin,
                      metaclass=SerializerMeta):
    pass


class PlaylistSerializer(ModelSerializer, PlaylistSerializerMixin,
                         metaclass=SerializerMeta):
    pass


class UserSerializer(ModelSerializer, UserSerializerMixin,
                     metaclass=SerializerMeta):
    pass
