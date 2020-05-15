from .base import Serializer, SerializerMeta, SerializerError, \
    SimpleSerializerMixin
from .model_helpers import ModelSerializerMixin, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin, SearchSerializerMixin, ProviderSerializerMixin


class PythonSerializer(Serializer):
    _mapping = {}

    def __init__(self, **options):
        super().__init__(**options)
        self.opt_level = options.get('level', 0)

    def serialize_items(self, items):
        json_ = {}
        for key, value in items:
            serializer_cls = PythonSerializer.get_serializer_cls(value)
            serializer = serializer_cls(brief=True, level=self.opt_level + 1)
            json_[key] = serializer.serialize(value)
        return json_


class ModelSerializer(PythonSerializer, ModelSerializerMixin):

    def __init__(self, **options):
        if options.get('brief') is False and options.get('fetch') is False:
            raise SerializerError(
                "fetch can't be False when brief is False")

        super().__init__(**options)
        self.opt_as_line = options.get('as_line', False)
        self.opt_brief = options.get('brief', True)
        self.opt_fetch = options.get('fetch', False)

        if self.opt_brief is False:
            self.opt_fetch = True

    def serialize(self, model):
        dict_ = {}
        for field, value in self._get_items(model):
            serializer_cls = self.get_serializer_cls(value)
            value_dict = serializer_cls(brief=True, fetch=False).serialize(value)
            dict_[field] = value_dict
        return dict_


#######################
# container serializers
#######################


class ListSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (list, )

    def serialize(self, list_):
        if not list_:
            return []
        item0 = list_[0]
        serializer_cls = PythonSerializer.get_serializer_cls(item0)
        if issubclass(serializer_cls, SearchSerializer):
            return self.serialize_search_result_list(list_)
        serializer = serializer_cls(brief=True, fetch=False)
        result = []
        for item in list_:
            result.append(serializer.serialize(item))
        return result

    def serialize_search_result_list(self, list_):
        serializer = SearchSerializer()
        return [serializer.serialize(model) for model in list_]


###################
# model serializers
###################


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


####################
# object serializers
####################


class SimpleTypeSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float, type(None))

    def serialize(self, object):
        return object


class ProviderSerializer(PythonSerializer,
                         SimpleSerializerMixin,
                         ProviderSerializerMixin,
                         metaclass=SerializerMeta):
    pass


class SearchSerializer(PythonSerializer, SearchSerializerMixin,
                       metaclass=SerializerMeta):

    def serialize(self, result):
        list_serializer = ListSerializer()
        json_ = {}
        for field, value in self._get_items(result):
            json_[field] = list_serializer.serialize(value)
        return json_
