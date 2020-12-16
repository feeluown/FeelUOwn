from .base import SerializerError

# format Serializer mapping, like::
#
# {
#    'json':  JsonSerializer,
#    'plain': PlainSerializer
# }
_MAPPING = {}


def register_serializer(type_, serializer_cls):
    _MAPPING[type_] = serializer_cls


def _load_serializers():
    register_serializer('plain', PlainSerializer)
    register_serializer('json', JsonSerializer)
    register_serializer('python', PythonSerializer)


def get_serializer(format):
    if not _MAPPING:
        _load_serializers()
    if format not in _MAPPING:
        raise SerializerError("Serializer for format:{} not found".format(format))
    return _MAPPING.get(format)


def serialize(format, obj, **options):
    """serialize python object defined in feeluown package

    :raises SerializerError:

    Usage::

        serialize('plain', song, as_line=True)
        serialize('plain', song, as_line=True, fetch=True)
        serialize('json', songs, indent=4)
        serialize('json', songs, indent=4, fetch=True)
        serialize('json', providers)
    """
    serializer = get_serializer(format)(**options)
    return serializer.serialize(obj)


from .base import SerializerMeta, SimpleSerializerMixin  # noqa
from .plain import PlainSerializer  # noqa
from .json_ import JsonSerializer  # noqa
from .python import PythonSerializer  # noqa
