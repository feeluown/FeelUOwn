import json

from .base import Serializer, SerializerMeta
from .model_helpers import serialize_model, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin


class JsonSerializer(Serializer):
    _mapping = {}


class ModelSerializer(JsonSerializer):

    def __init__(self, **options):
        super().__init__(**options)

    def serialize(self, model):
        # maybe we should add format option: `indent`,
        # currently, use 4 as default should be good enough?
        return serialize_model(model, self)

    def setup(self):
        self._json = {}

    def before_handle_field(self, model, fields):
        pass

    def handle_field(self, field, value):
        self._json[field] = value

    def after_handle_field(self, model, fields):
        pass

    def get_result(self):
        return self._json

    def teardown(self):
        del self._json


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
