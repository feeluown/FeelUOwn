"""
model/uri transform

TODO: move feeluown.server.rpc.model_parser to feeluown.library.parser

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
import logging
import json
import re
import warnings

from .base import ModelType
from .model_state import ModelState
from .models import get_modelcls_by_type


logger = logging.getLogger(__name__)


class ResolveFailed(Exception):
    pass


class ResolverNotFound(Exception):
    # TODO: use ResolveFailed instead
    pass


class NoReverseMatch(Exception):
    pass


# TODO: maybe expose a API like get_type_by_ ?
TYPE_NS_MAP = {
    ModelType.song: 'songs',
    ModelType.artist: 'artists',
    ModelType.album: 'albums',
    ModelType.playlist: 'playlists',
    ModelType.user: 'users',
    ModelType.lyric: 'lyrics',
    ModelType.video: 'videos',
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


DELIMETER = ' - '


def quote_field(field: str) -> str:
    r"""quote field which contains DELIMETER

    >>> quote_field('决定')
    '决定'
    >>> quote_field('决"定')
    '决"定'
    >>> quote_field('决 - 定')
    '"决 - 定"'
    >>> quote_field('决" - 定')   # "决\" - 定"
    '"决\\" - 定"'
    """
    if not field:
        return '""'
    if field.startswith('"') or field.find(DELIMETER) != -1:
        return json.dumps(field, ensure_ascii=False)
    return field


def unquote_field(field):
    return json.loads(field)


quoted_delim_re = re.compile(rf'"([^"\\]*(?:\\.[^"\\]*)*)"?{DELIMETER}', re.S)
normal_delim_re = re.compile(rf'.*?{DELIMETER}')
quoted_eof_re = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"$', re.S)
normal_eof_re = re.compile(r'.+$')


class TokenType:
    quoted_delim = 0
    quoted_eof = 1
    normal_delim = 2
    normal_eof = 3


def _split(s: str, num: int) -> list:
    """

    # backward compat
    >>> _split('約束（Cover：リリィ、… - Akie秋绘 -  - ', 4)
    ['約束（Cover：リリィ、…', 'Akie秋绘', '', '']
    >>> _split('没有人知道 - 李宗盛', 4)
    ['没有人知道', '李宗盛', '', '']

    # when the trailing whitespace is deleted by user
    >>> _split('Flower Dance - DJ OKAWARI -  -', 4)
    ['Flower Dance', 'DJ OKAWARI', '', '']

    >>> _split('Flower Dance - DJ OKAWARI - "" - ""', 4)
    ['Flower Dance', 'DJ OKAWARI', '', '']
    >>> _split('Flower Dance - DJ OKAWARI - ""', 4)
    ['Flower Dance', 'DJ OKAWARI', '', '']
    """
    # when the trailing whitespace is deleted by accident,
    # we just delete the DELIMTER part
    if s.endswith(' -'):
        s = s[:-2]

    rules = [(TokenType.quoted_delim, quoted_delim_re),
             (TokenType.quoted_eof, quoted_eof_re),
             (TokenType.normal_delim, normal_delim_re),
             (TokenType.normal_eof, normal_eof_re)]

    fields = []
    pos = 0
    while True:
        for rule in rules:
            token_type, regex = rule
            m = regex.match(s, pos)
            if m is None:
                continue

            # handle value by token type
            value = m.group()
            if token_type is TokenType.quoted_delim:
                fields.append(unquote_field(value[:-3]))
            elif token_type is TokenType.quoted_eof:
                fields.append(unquote_field(value))

            elif token_type is TokenType.normal_delim:
                fields.append(value[:-3])
            else:  # TokenType.delim_eof
                fields.append(value)

            pos = m.end()
            break
        else:
            if pos != len(s):
                raise ValueError('invalid fields string')
            else:
                break

    if len(fields) != num:
        current = len(fields)
        if current < num:
            fields.extend([''] * (num - current))

    return fields


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


def parse_video_str(video_str):
    values = _split(video_str, 1)
    return {
        'title': values[0]
    }


def parse_unknown(_):
    return {}


def parse_line(line):
    """parse text line and return a model instance

    >>> line = 'fuo://xxx/songs/1  # 没有人知道 - 李宗盛'
    >>> model, _ = parse_line(line)
    >>> model.source, model.title_display
    ('xxx', '没有人知道')
    >>> line = 'fuo://xxx/songs/1-1'
    >>> model, _ = parse_line(line)
    >>> model.identifier
    '1-1'
    """
    line = line.strip()
    parts = line.split('#', maxsplit=1)
    if len(parts) == 2:
        uri, model_str = parts
    else:
        uri, model_str = parts[0], ''
    ns_list = list(TYPE_NS_MAP.values())
    p = re.compile(r'^fuo://(\w+)/({})/([\w-]+)'.format('|'.join(ns_list)))
    uri = uri.strip()
    m = p.match(uri)
    if not m:
        raise ResolveFailed('invalid line: {}'.format(line))
    source, ns, identifier = m.groups()
    path = uri[m.end():]
    Model = get_modelcls_by_type(NS_TYPE_MAP[ns], brief=True)
    if ns == 'songs':
        parse_func = parse_song_str
    elif ns == 'albums':
        parse_func = parse_album_str
    elif ns == 'artists':
        parse_func = parse_artist_str
    elif ns == 'videos':
        parse_func = parse_video_str
    else:
        parse_func = parse_unknown
    data = parse_func(model_str.strip())
    data['source'] = source
    model = Model(identifier=identifier, **data)
    return model, path


def resolve(line, model=None):
    """

    for example, line can be 'fuo://local/songs/1/cover/data'
    """
    from feeluown.library import get_modelcls_by_type, V2SupportedModelTypes

    if model is None:
        model, path = parse_line(line)
        library = Resolver.library
        provider = library.get(model.source)
        if provider is None:
            model.state = ModelState.not_exists
        else:
            model_type = ModelType(model.meta.model_type)
            modelcls = get_modelcls_by_type(model_type, brief=True)
            assert modelcls is not None and model_type in V2SupportedModelTypes
    else:
        path = line
    # NOTE: the path resolve logic is deprecated
    if path:
        warnings.warn('model path resolver will be removed')
        paths = getattr(model.meta, 'paths', [])
        for path_ in paths:
            if path_ == path:
                method_name = 'resolve_' + path.replace('/', '_')
                handler = getattr(model, method_name)
                return handler()
        raise ResolverNotFound(
            'resolver-not-found for {}/{}'.format(str(model), path))
    return model


def reverse(model, path='', as_line=False):
    if path:
        warnings.warn('model path resolver will be removed')
        paths = getattr(model.meta, 'paths', [])
        if path not in paths and path[1:] not in model.model_fields:
            raise NoReverseMatch(f'no-reverse-match for model:{model} path:{path}')

    source = model.source
    ns = TYPE_NS_MAP[model.meta.model_type]
    identifier = model.identifier
    uri = 'fuo://{}/{}/{}'.format(source, ns, identifier)
    text = uri + (path if path else '')
    if as_line:
        if model.meta.model_type == ModelType.song:
            song = model
            fields = [song.title_display,
                      song.artists_name_display,
                      song.album_name_display,
                      song.duration_ms_display]
        elif model.meta.model_type == ModelType.album:
            album = model
            fields = [album.name_display,
                      album.artists_name_display]
        elif model.meta.model_type == ModelType.artist:
            artist = model
            fields = [artist.name_display]
        elif model.meta.model_type == ModelType.video:
            video = model
            fields = [video.title_display]
        else:
            logger.warn('The display fields are dropped during reverse')
            fields = []

        # strip emtpy suffix
        for field in reversed(fields):
            if not field:
                fields.pop(-1)
            else:
                break

        if fields and any((bool(f) for f in fields)):
            model_str = DELIMETER.join([quote_field(f) for f in fields])
            text += '\t# '
            text += model_str
    return text
