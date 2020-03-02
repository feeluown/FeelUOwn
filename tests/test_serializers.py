from fuocore.serializers import serialize
from fuocore.provider import dummy_provider, Dummy


def test_serialize_models():
    for cls_name in ('Song', 'Album', 'Playlist', 'Artist', 'User',):
        model = getattr(dummy_provider, cls_name).get(Dummy)
        for format in ('plain', 'json'):
            serialize(format, model)
            serialize(format, model, as_line=True)
            serialize(format, model, as_line=True, fetch=True)
            serialize(format, model, as_line=False, brief=True, fetch=True)


def test_serialize_provider():
    for format in ('plain', 'json'):
        serialize(format, dummy_provider, brief=False)
        serialize(format, dummy_provider, as_line=True)


def test_serialize_providers():
    for format in ('plain', 'json'):
        serialize(format, [dummy_provider], brief=False)
        serialize(format, [dummy_provider])
