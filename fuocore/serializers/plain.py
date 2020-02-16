"""
Usage::

    serializer = PlainSerializer(**options)
    text = serializer.serialize(model)

    song_serializer = SongPlainSerializer(**options)
    text = song_serializer.serialize(model)
"""

from .base import Serializer, SerializerMeta
from .model_helpers import ModelSerializerMixin, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin
from ._plain_formatter import WideFormatter

formatter = WideFormatter()
fmt = formatter.format


class PlainSerializer(Serializer):
    _mapping = {}


class ModelSerializer(ModelSerializerMixin, PlainSerializer):

    def __init__(self, **options):
        super().__init__(**options)

        # format options
        self._as_line = options.get('as_line', True)
        self._uri_length = options.get('uri_length', '')

    def setup(self, model, fields):
        if self._as_line:
            self._store = {}
        else:
            key_length = max(len(key) for key in fields) + 1
            self._key_length = key_length
            self._normal_field_tpl = '{key:>%d}:  {value}' % key_length
            self._list_field_tpl = '{key:>%d}::' % (key_length - 1)

    def handle_field(self, field, value):
        if self._as_line:
            self._store[field] = value
        else:
            if isinstance(value, list):
                # append key
                text = fmt(self._list_field_tpl, key=field)
                self._text_list.append(text)
                # append value
                if value:
                    padding = ' ' * (self._key_length + 3)
                    self._text_list.extend(
                        (padding + line for line in value.split('\n')))
            else:
                text = fmt(self._normal_field_tpl, key=field, value=value)
                self._text_list.append(text)

    def get_result(self):
        if self._as_line:
            return fmt(self._line_fmt,
                       uri_length=self._uri_length,
                       **self._store)
        return '\n'.join(self._text_list)

    def teardown(self):
        if self._as_line:
            del self._store
        else:
            del self._key_length
            del self._text_list
            del self._normal_field_tpl
            del self._list_field_tpl


class SimpleTypePlainSerializer(PlainSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float)

    def serialize(self, object):
        return object


class ListPlainSerializer(PlainSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (list, )

    def serialize(self, list_):
        if not list_:
            return ''
        item0 = list_[0]
        serializer_cls = PlainSerializer.get_serializer_cls(item0)
        if isinstance(serializer_cls, ModelSerializer):
            # FIXME: use reverse
            uri_length = max(len(str(item)) for item in list_)
            serializer = serializer_cls(as_line=True, uri_length=uri_length)
        else:
            serializer = serializer_cls(as_line=True)
        text_list = []
        for item in list_:
            text_list.append(serializer.serialize(item))
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
