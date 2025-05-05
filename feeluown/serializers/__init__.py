from .base import SerializerError, DeserializerError

# format Serializer mapping, like::
#
# {
#    'json':  JsonSerializer,
#    'plain': PlainSerializer
# }
_MAPPING = {}
_DE_MAPPING = {}


def register_serializer(type_, serializer_cls):
    _MAPPING[type_] = serializer_cls


def register_deserializer(type_, deserializer_cls):
    _DE_MAPPING[type_] = deserializer_cls


def get_serializer(format_):
    if not _MAPPING:
        register_serializer('plain', PlainSerializer)
        register_serializer('json', JsonSerializer)
        register_serializer('python', PythonSerializer)
    if format_ not in _MAPPING:
        raise SerializerError(f"Serializer for format:{format_} not found")
    return _MAPPING.get(format_)


def get_deserializer(format_: str):
    if not _DE_MAPPING:
        register_deserializer('python', PythonDeserializer)
    if format_ not in _DE_MAPPING:
        raise DeserializerError(f"Deserializer for format:{format_} not found")
    return _DE_MAPPING[format_]


def serialize(format_, obj, **options):
    """serialize python object defined in feeluown package

    :raises SerializerError:

    Usage::

        serialize('plain', song, as_line=True)
        serialize('plain', song, as_line=True, fetch=True)
        serialize('json', songs, indent=4)
        serialize('json', songs, indent=4, fetch=True)
        serialize('json', providers)
    """
    serializer = get_serializer(format_)(**options)
    return serializer.serialize(obj)


def deserialize(format_, obj, **options):
    deserializer = get_deserializer(format_)(**options)
    return deserializer.deserialize(obj)


from .base import SerializerMeta, SimpleSerializerMixin  # noqa
from .plain import PlainSerializer  # noqa
from .json_ import JsonSerializer  # noqa
from .python import PythonSerializer, PythonDeserializer  # noqa
from .objs import *  # noqa
