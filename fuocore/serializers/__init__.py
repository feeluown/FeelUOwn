# ObjectType Serializer mapping
#
# {
#    int:  XSerializer,
#    BaseModel: ModelSerializer,
#    Provider: ProviderSerializer,
# }
#
import json

_MAPPING = {}


def register_serializer(type_, serializer_cls):
    _MAPPING[type_] = serializer_cls


def _load_serializers():
    register_serializer('plain', PlainSerializer)
    register_serializer('json', JsonSerializer)


def get_serializer(format):
    if not _MAPPING:
        _load_serializers()
    return _MAPPING.get(format)


def serialize(format, obj, dump=False, **options):
    """

    Usage::

        # serialize song
        # real use case: fuo show fuo://local/songs/1
        serialize('plain', song)
        serialize('plain', song, brief=False, fetch=True)
        serialize('plain', song, brief=False, fetch=False)

        # serialize song to a single line
        # real use case: fuo play fuo://local/songs/1
        serialize('plain', song, as_line=True)
        serialize('plain', song, as_line=True, fetch=True)

        # serialize songs
        # real use case: fuo show fuo://local/playlist/1/songs
        #   currently, this should never fetch each song detail,
        #   even we set fetch to True.
        serialize('plain', songs)

        # serialize song in json format
        serialize('json', song)
        serialize('json', song, brief=False, fetch=True)

        # serialize list of provider
        serialize('json', providers)

    **Options**

    - fields related options: `brief`, `fetch`
    - format related options: `as_line`
    """
    serializer = get_serializer(format)(**options)
    result = serializer.serialize(obj)
    if dump and format == 'json':
        return json.dumps(result, indent=4)
    return result


from .plain import PlainSerializer  # noqa
from .json_ import JsonSerializer  # noqa
