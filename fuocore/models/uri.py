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
import logging
from enum import Enum

from fuocore.models import ModelType, ModelExistence
from fuocore.provider import dummy_provider


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


# def _model_unescape(model_str):
#     # \- => -
#     return model_str.replace('\\-', '-').replace('\\\\', '\\')
#
#
# def _model_escape(model_str):
#     # - => \-
#     return model_str.replace('\\', '\\\\').replace('-', '\\-')
#

def _field_unescape(filed: str) -> str:
    # '"\" \" \\"' => '" " \'
    if len(filed) >= 2 and filed.startswith('"') and filed.endswith('"'):
        filed = filed.replace('\\"', '"').replace('\\\\', '\\')
    return filed


def _field_escape(filed: str) -> str:
    # 如果字段中存在'-',则进行转义
    if filed.find('-') != -1:
        filed = filed.replace('\\', '\\\\').replace('"', '\\"')
        return '"{}"'.format(filed)
    return filed


# def _split(s, num):
#     # 这里使用'- '的原因是为了解决:无网络条件下无法获取在线歌曲时长,
#     # 导致写出格式存在问题,之前的_split无法解析下列异常情况
#     # 'fuo://xiami/songs/1769834090	# Flower Dance - DJ OKAWARI -  -'
#     # FIXME:修改写入部分的代码,而不是hack parse 过程
#     DELIMITER = ' -'
#     values = s.split(DELIMITER)
#     values = [v.strip() for v in values]
#     current = len(values)
#     if current < num:
#         values.extend([''] * (num - current))
#     return values


def _split(s: str, num: int) -> list:
    class ParseState(Enum):
        # 寻找下一个字段
        find_next_filed = 0
        # 解析字段
        parse_normal_filed = 1
        # 解析转义字段
        parse_quoted_filed = 2
        # 解析分隔符
        parse_delimiter = 3

    # filed1 - filed2 - filed3 - "filed4"
    parse_state = ParseState.find_next_filed

    fields = []
    field = ""
    # TODO:修复类似这样的解析"Flower Dance - DJ OKAWARI -  - "
    # 特别注意这种形式"Flower Dance - DJ OKAWARI -  - 4:23"
    # 中间字段的空白可能导致解析错位
    s += '\n'
    for ch in s:
        if parse_state is ParseState.find_next_filed:
            if ch == ' ' or ch == '\n':
                continue
            if ch == '"':
                parse_state = ParseState.parse_quoted_filed
            else:
                parse_state = ParseState.parse_normal_filed
                field += ch
        elif parse_state is ParseState.parse_normal_filed:
            if ch == '\n':
                fields.append(field)
                field = ""
            elif ch == '-':
                # TODO:去除末尾空格
                fields.append(field)
                field = ""
                parse_state = ParseState.find_next_filed
            else:
                field += ch
        elif parse_state is ParseState.parse_quoted_filed:
            if ch == '"':
                fields.append(field)
                field = ""
                parse_state = ParseState.parse_delimiter
            else:
                field += ch
        elif parse_state is ParseState.parse_delimiter:
            if ch == '-':
                parse_state = ParseState.find_next_filed
    if len(fields) != num:
        current = len(fields)

        logging.warning(
            '_split("{}") expect to get {} fields,'.format(s, num, )
            + 'but get {} fields:\n{}'.format(current, fields))

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
    """
    line = line.strip()
    parts = line.split('#', maxsplit=1)
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
    elif ns == 'videos':
        parse_func = parse_video_str
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
            model.exists = ModelExistence.no
        else:
            model_cls = provider.get_model_cls(model.meta.model_type)
            model = model_cls(model)
    else:
        path = line
    if path:
        for path_ in model.meta.paths:
            if path_ == path:
                method_name = 'resolve_' + path.replace('/', '_')
                handler = getattr(model, method_name)
                return handler()
        raise ResolverNotFound(
            'resolver-not-found for {}/{}'.format(str(model), path))
    return model


def do_reverse(fields: list) -> str:
    length = len(fields)
    if length == 0:
        return ""
    line = ""
    for field in fields[0:-1]:
        if not field:
            field = ' '
        line += _field_escape(field) + ' - '
    line += fields[-1] if fields[-1] else ' '
    return line


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
            model_str = do_reverse(
                [
                    song.title_display,
                    song.artists_name_display,
                    song.album_name_display,
                    song.duration_ms_display
                ]
            )
        elif model.meta.model_type == ModelType.album:
            album = model
            model_str = do_reverse(
                [
                    album.name_display,
                    album.artists_name_display
                ]
            )

        elif model.meta.model_type == ModelType.artist:
            artist = model
            model_str = do_reverse(
                [artist.name_display]
            )
        else:
            model_str = ''
        if model_str:
            text += '\t# '
            text += model_str
    return text
