from textwrap import indent
# FIXME: maybe we should move `reverse` into serializers package
from .base import Serializer, SerializerMeta, SerializerError
from ._plain_formatter import WideFormatter

from feeluown.library import (
    reverse,
    BaseModel,
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    UserModel,
    BriefSongModel,
    BriefArtistModel,
    BriefAlbumModel,
    BriefPlaylistModel,
    BriefUserModel,
)

formatter = WideFormatter()
fmt = formatter.format


class ModelSerializerMixin:

    def _get_items(self, model):
        # initialize fields that need to be serialized
        # if as_line option is set, we always use fields_display
        modelcls = type(model)
        fields = [field for field in model.model_fields
                  if field not in BaseModel.model_fields]
        # Include properties.
        pydantic_fields = ("__values__", "fields", "__fields_set__",
                           "model_computed_fields", "model_extra",
                           "model_fields_set")
        fields += [prop for prop in dir(modelcls)
                   if isinstance(getattr(modelcls, prop), property)
                   and prop not in pydantic_fields]
        items = [("provider", model.source),
                 ("identifier", str(model.identifier)),
                 ("uri", reverse(model))]
        for field in fields:
            items.append((field, getattr(model, field)))
        return items


class SongSerializerMixin:
    class Meta:
        types = (SongModel, BriefSongModel)
        # since url can be too long, we put it at last
        fields = ('title', 'duration', 'album', 'artists')
        line_fmt = '{uri:{uri_length}}\t# {title:_18} - {artists_name:_20}'


class ArtistSerializerMixin:
    class Meta:
        types = (ArtistModel, BriefArtistModel)
        fields = ('name', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class AlbumSerializerMixin:
    class Meta:
        types = (AlbumModel, BriefAlbumModel)
        fields = ('name', 'artists', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_18} - {artists_name:_20}'


class PlaylistSerializerMixin:
    class Meta:
        types = (PlaylistModel, BriefPlaylistModel)
        fields = ('name',)
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class UserSerializerMixin:
    class Meta:
        types = (UserModel, BriefUserModel)
        fields = ('name', 'playlists')
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class PlainSerializer(Serializer):
    """PlainSerializer base class"""
    _mapping = {}

    def __init__(self, **options):
        super().__init__(**options)
        self.opt_level = options.get('level', 0)

    def serialize_items(self, items):
        key_length = max(len(key) for key, _ in items)
        normal_field_tpl = '{key:>%d}:  {value}' % (key_length + 1)
        list_field_tpl = '{key:>%d}::' % (key_length)
        text_list = []
        level = self.opt_level + 1
        for field, value in items:
            if isinstance(value, list):
                # append key
                text = fmt(list_field_tpl, key=field)
                text_list.append(text)
                # append value with indent
                if value:
                    serialize_cls = self.get_serializer_cls(value)
                    serializer = serialize_cls(fetch=False, level=level)
                    value_text = serializer.serialize(value)
                    text_list.append(indent(value_text, ' ' * (key_length + 4)))
            else:
                serialize_cls = self.get_serializer_cls(value)
                # field value should be formatted as one line
                serializer = serialize_cls(fetch=False, level=level)
                value_text = serializer.serialize(value)
                text = fmt(normal_field_tpl, key=field, value=value_text)
                text_list.append(text)
        return '\n'.join(text_list)


class ModelSerializer(PlainSerializer, ModelSerializerMixin):

    def __init__(self, **options):
        # do some validation
        if all([options.get('as_line') is False,
                options.get('brief') is False,
                options.get('fetch') is False]):
            raise SerializerError(
                "as_line, brief, fetch can't be false at same time")
        if options.get('as_line') is True and options.get('brief') is False:
            raise SerializerError(
                "brief can't be False when as_line is True")
        if options.get('brief') is False and options.get('fetch') is False:
            raise SerializerError(
                "fetch can't be False when brief is False")

        super().__init__(**options)
        self.opt_as_line = options.get('as_line', False)
        self.opt_brief = options.get('brief', True)
        self.opt_fetch = options.get('fetch', not self.opt_brief)
        self.opt_uri_length = options.get('uri_length', '')

    def serialize(self, model):
        """serialize a model"""
        items = self._get_items(model)
        # if level > 0, we think this should be formatted as one line,
        # subclass can override this behavious by overriding serialize method
        if self.opt_as_line or self.opt_level > 0:
            return fmt(self._line_fmt, uri_length=self.opt_uri_length, **dict(items))
        return self.serialize_items(items)


class ListSerializer(PlainSerializer, metaclass=SerializerMeta):
    """
    Theoretically, we should have ListTypeSerializer for each object type,
    but many of these object have exact same serialization logic.

    SearchModel is an exception.
    """

    class Meta:
        types = (list,)

    def serialize(self, list_):
        from .objs import SearchPlainSerializer

        if not list_:
            return ''
        item0 = list_[0]
        serializer_cls = PlainSerializer.get_serializer_cls(item0)
        level = self.opt_level + 1
        if issubclass(serializer_cls, ModelSerializer):
            if issubclass(serializer_cls, SearchPlainSerializer):
                return self.serialize_search_result_list(list_)
            uri_length = max(len(reverse(item)) for item in list_)
            serializer = serializer_cls(fetch=False, level=level,
                                        uri_length=uri_length, )
        else:
            # list item should be formatted as one line
            serializer = serializer_cls(fetch=False, level=level)
        text_list = []
        for item in list_:
            serialized_item = serializer.serialize(item)
            if serialized_item:
                text_list.append(serialized_item)

        return '\n'.join(text_list)

    def serialize_search_result_list(self, list_):
        from .objs import SearchPlainSerializer

        serializer = SearchPlainSerializer(
            level=self.opt_level + 1,
            fetch=False,
            brief=True,
            as_line=False
        )
        # calculate max uri_length
        max_uri_length = 0
        for model in list_:
            max_uri_length = max(serializer.calc_max_uri_length(model),
                                 max_uri_length)
        serializer.opt_uri_length = max_uri_length
        text_list = [serializer.serialize(model) for model in list_]
        return '\n'.join(text_list)


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


class SimpleTypeSerializer(PlainSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float, type(None), bool)

    def serialize(self, object):
        if object is None:
            return 'null'
        elif object is True:
            return 'true'
        elif object is False:
            return 'false'
        return str(object)
