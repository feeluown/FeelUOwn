from .base import Serializer, SerializerMeta, SerializerError
from .model_helpers import ModelSerializerMixin, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin


class PythonSerializer(Serializer):
    _mapping = {}


class ModelSerializer(PythonSerializer, ModelSerializerMixin):

    def __init__(self, **options):
        if options.get('brief') is False and options.get('fetch') is False:
            raise SerializerError(
                "fetch can't be False when brief is False")

        super().__init__(**options)
        self.options['as_line'] = options.get('as_line', False)
        self.options['brief'] = options.get('brief', True)
        self.options['fetch'] = options.get('fetch', False)

        if self.options['brief'] is False:
            self.options['fetch'] = True

    def serialize(self, model):
        dict_ = {}
        for field, value in self._get_items(model):
            serializer_cls = self.get_serializer_cls(value)
            value_dict = serializer_cls(brief=True, fetch=False).serialize(value)
            dict_[field] = value_dict
        return dict_


class ListSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (list, )

    def serialize(self, list_):
        if not list_:
            return []
        item0 = list_[0]
        serializer_cls = PythonSerializer.get_serializer_cls(item0)
        serializer = serializer_cls(brief=True, fetch=False)
        result = []
        for item in list_:
            result.append(serializer.serialize(item))
        return result


class SimpleTypePlainSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float, type(None))

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
