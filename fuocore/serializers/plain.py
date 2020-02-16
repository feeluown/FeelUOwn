"""
Usage::

    serializer = PlainSerializer(**options)
    text = serializer.serialize(model)

    song_serializer = SongPlainSerializer(**options)
    text = song_serializer.serialize(model)
"""

from textwrap import indent
from .base import Serializer, SerializerMeta, InvalidOptionsCombination
from .model_helpers import ModelSerializerMixin, SongSerializerMixin, \
    ArtistSerializerMixin, AlbumSerializerMixin, PlaylistSerializerMixin, \
    UserSerializerMixin
from ._plain_formatter import WideFormatter

formatter = WideFormatter()
fmt = formatter.format


class PlainSerializer(Serializer):
    _mapping = {}


class ModelSerializer(PlainSerializer, ModelSerializerMixin):

    def __init__(self, **options):
        # do some validation
        if all([options.get('as_line') is False,
                options.get('brief') is False,
                options.get('fetch') is False]):
            raise InvalidOptionsCombination(
                    "as_line, brief, fetch can't be false at same time")
        if options.get('as_line') is True and options.get('brief') is False:
            raise InvalidOptionsCombination(
                "brief can't be False when as_line is True")
        if options.get('brief') is False and options.get('fetch') is False:
            raise InvalidOptionsCombination(
                "fetch can't be False when brief is False")

        super().__init__(**options)

        self._as_line = options.get('as_line', True)
        if self._as_line is True:
            self.options['brief'] = True
        if self.options['brief'] is False:
            self.options['fetch'] = True
        self._uri_length = options.get('uri_length', '')

    def serialize(self, model):
        items = self._get_items(model)
        if self._as_line:
            return fmt(self._line_fmt, uri_length=self._uri_length, **dict(items))

        key_length = max(len(key) for key, _ in items) + 1
        normal_field_tpl = '{key:>%d}:  {value}' % key_length
        list_field_tpl = '{key:>%d}::' % (key_length - 1)
        text_list = []
        for field, value in items:
            if isinstance(value, list):
                # append key
                text = fmt(list_field_tpl, key=field)
                text_list.append(text)
                # append value with indent
                if value:
                    serialize_cls = self.get_serializer_cls(value)
                    value_text = serialize_cls(fetch=False).serialize(value)
                    text_list.append(indent(value_text, ' ' * (key_length + 3)))
            else:
                serialize_cls = self.get_serializer_cls(value)
                value_text = serialize_cls(as_line=True, fetch=False).serialize(value)
                text = fmt(normal_field_tpl, key=field, value=value_text)
                text_list.append(text)
        return '\n'.join(text_list)


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
            serializer = serializer_cls(as_line=True, fetch=False,
                                        uri_length=uri_length)
        else:
            serializer = serializer_cls(as_line=True, fetch=False)
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
