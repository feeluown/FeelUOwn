"""
model/uri transform

TODO: move fuocore.protocol.model_parser to fuocore.models.parser

.. warn::

   currently, the design of uri module is under investigation,
   we should only use only it in local provider.

experience:

1. Models should explicitly tell user what they support.
For exmaple: if a artist model support '/albums?type=eq',
the model should desclare they support type filter.
Currently, there is not way to achieve this.
"""

import asyncio
import re

from fuocore.models import ModelType
from fuocore.provider import dummy_provider


class ResolveFailed(Exception):
    pass


class ResolverNotFound(Exception):
    pass


class NoReverseMatch(Exception):
    pass


TYPE_NS_MAP = {
    ModelType.song: 'songs',
    ModelType.artist: 'artists',
    ModelType.album: 'albums',
    ModelType.playlist: 'playlists',
    ModelType.user: 'users',
    ModelType.lyric: 'lyrics',
}
NS_TYPE_MAP = {
    value: key
    for key, value in TYPE_NS_MAP.items()
}


class Resolver:

    loop = None
    library = None

    @classmethod
    def setup_aio_support(cls):
        cls.loop = asyncio.get_event_loop()


def _split(s, num):
    DELIMITER = ' - '
    values = s.split(DELIMITER)
    current = len(values)
    if current < num:
        values.extend([''] * (num - current))
    return values


def parse_song_str(song_str):
    values = _split(song_str, 4)
    return {
        'title': values[0],
        'artists_name': values[1],
        'album_name': values[2],
        'duration_ms': values[3]
    }


def parse_album_str(album_str):
    values = _split(album_str, 2)
    return {
        'name': values[0],
        'artists_name': values[1]
    }


def parse_artist_str(album_str):
    values = _split(album_str, 1)
    return {
        'name': values[0],
    }


def parse_unknown(_):
    return {}


def parse_line(line):
    """parse text line and return a model instance

    >>> line = 'fuo://xxx/songs/1  # 没有人知道 - 李宗盛'
    >>> model, _ = parse_line(line)
    >>> model.source, model.title_display
    ('xxx', '没有人知道')
    """
    line = line.strip()
    parts = line.split('#')
    if len(parts) == 2:
        uri, model_str = parts
    else:
        uri, model_str = parts[0], ''
    ns_list = list(TYPE_NS_MAP.values())
    p = re.compile(r'^fuo://(\w+)/({})/(\w+)'.format('|'.join(ns_list)))
    uri = uri.strip()
    m = p.match(uri)
    if not m:
        raise ResolveFailed('invalid line: {}'.format(line))
    source, ns, identifier = m.groups()
    path = uri[m.end():]
    Model = dummy_provider.get_model_cls(NS_TYPE_MAP[ns])
    if ns == 'songs':
        parse_func = parse_song_str
    elif ns == 'albums':
        parse_func = parse_album_str
    elif ns == 'artists':
        parse_func = parse_artist_str
    else:
        parse_func = parse_unknown
    data = parse_func(model_str.strip())
    model = Model.create_by_display(identifier=identifier, **data)
    model.source = source
    return model, path


def resolve(line, model=None):
    """

    for example, line can be 'fuo://local/songs/1/cover/data'
    """
    if model is None:
        model, path = parse_line(line)
        library = Resolver.library
        provider = library.get(model.source)
        if provider is None:
            raise ResolverNotFound('provider not found: {}'.format(model.source))
        data = {}
        for field in model.meta.fields_display:
            data[field] = getattr(model, field + '_display', '')
        model_cls = provider.get_model_cls(model.meta.model_type)
        model = model_cls.create_by_display(identifier=model.identifier, **data)
    else:
        path = line
    if path:
        for path_ in model.meta.paths:
            if path_ == path:
                method_name = 'resolve_' + path.replace('/', '_')
                handler = getattr(model, method_name)
                return handler()
        raise ResolverNotFound('resolver-not-found for {}/{}'.format(str(model), path))
    return model


def reverse(model, path='', as_line=False):
    if path:
        if path not in model.meta.paths and path[1:] not in model.meta.fields:
            raise NoReverseMatch('no-reverse-match for model:{} path:{}'
                                 .format(model, path))
    source = model.source
    ns = TYPE_NS_MAP[model.meta.model_type]
    identifier = model.identifier
    uri = 'fuo://{}/{}/{}'.format(source, ns, identifier)
    text = uri + (path if path else '')
    if as_line:
        if model.meta.model_type == ModelType.song:
            song = model
            model_str = '{} - {} - {} - {}'.format(
                song.title_display,
                song.artists_name_display,
                song.album_name_display,
                song.duration_ms_display
            )
        elif model.meta.model_type == ModelType.album:
            album = model
            model_str = '{} - {}'.format(
                album.name_display,
                album.artists_name_display
            )

        elif model.meta.model_type == ModelType.artist:
            artist = model
            model_str = '{}'.format(artist.name_display)
        else:
            model_str = ''
        if model_str:
            text += '\t# '
            text += model_str
    return text
