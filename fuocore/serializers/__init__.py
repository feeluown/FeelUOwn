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


def get_serializer(format):
    if not _MAPPING:
        _load_serializers()
    if format not in _MAPPING:
        raise SerializerError("Serializer for format:{} not found".format(format))
    return _MAPPING.get(format)


def serialize(format, obj, **options):
    """

    Usage::

        # serialize song
        # real use case: fuo show fuo://local/songs/1
        serialize('plain', song)

        # serialize song to a single line
        # real use case: fuo play fuo://local/songs/1
        serialize('plain', song, as_line=True, fetch=True)

        # serialize songs
        # real use case: fuo show fuo://local/playlist/1/songs
        #   currently, this should never fetch each song detail,
        #   even we set fetch to True.
        serialize('plain', songs)

        # serialize list of provider
        serialize('json', providers)

    **Options**

    - fields related options: `brief`, `fetch`
    - format related options: `as_line`
    """
    serializer = get_serializer(format)(**options)
    return serializer.serialize(obj)


from .plain import PlainSerializer  # noqa
from .json_ import JsonSerializer  # noqa
