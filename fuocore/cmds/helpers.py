"""
fuocore.cmds.helper
~~~~~~~~~~~~~~~~~~~

良好的用文字展示一个对象

展示的时候需要注意以下几点：
1. 让 awk、grep 等 shell 工具容易处理

TODO: 让代码长得更好看
"""

import json
from itertools import chain
from typing import Optional, Generator, Union, Type

from fuocore.models import BaseModel
from fuocore.models.uri import reverse
from fuocore.utils import _fit_text, WideFormatter


class RenderNode:
    model: BaseModel
    options: dict
    def __init__(self, model: BaseModel, **options):
        self.model = model
        self.options = options


def dict_walker(indict: dict, path: Optional[list] = None) -> Generator:
    path = path[:] if path else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in dict_walker(value, path + [key]):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                for i, v in enumerate(value):
                    for d in dict_walker(v, path + [key] + [i]):
                        yield d
            else:
                yield path + [key], value
    else:
        yield path, indict


def set_item_by_path(indict: dict, path: list, value):
    for key in path[:-1]:
        indict = indict.setdefault(key, {})
    indict[path[-1]] = value


class Serializer:
    _data: Union[RenderNode, BaseModel, dict]
    @classmethod
    def _render(cls, obj: BaseModel, **options) -> Union[str, dict]:
        raise NotImplementedError

    @classmethod
    def _serialize(cls, obj) -> dict:
        is_complete = False
        while not is_complete:
            is_complete = True
            for elem in dict_walker(obj):
                path, value = elem

                rendered = None
                if isinstance(value, RenderNode):
                    rendered = cls._render(value.model, **value.options)
                elif isinstance(value, BaseModel):
                    rendered = cls._render(value)

                if rendered:
                    set_item_by_path(obj, path, rendered)
                    is_complete = False
                    break
        return obj

    def __init__(self, data: Union[RenderNode, BaseModel, dict]):
        self._data = {"root": data}

    def serialize(self) -> dict:
        return self._serialize(self._data)["root"]


class PlainSerializer(Serializer):
    @classmethod
    def _render(cls, obj: BaseModel, **options) -> Union[str, dict]:
        if options.get("brief", True):
            return {"uri": str(obj), "info": obj.to_str(**options)}
        return obj.to_dict(**options)


class JsonSerializer(Serializer):
    @classmethod
    def _render(cls, obj: BaseModel, **options) -> Union[str, dict]:
        return obj.to_dict(**options)


class Emitter:
    data: dict
    def __init__(self, data: dict):
        self._data = data

    def emit(self) -> str:
        raise NotImplementedError


class JsonEmitter(Emitter):
    def emit(self) -> str:
        return json.dumps(self._data, indent=4, ensure_ascii=False)


class PlainEmitter(Emitter):
    formatter = WideFormatter()


    @classmethod
    def _list_g(cls, obj, indent='') -> Generator:
        uri_len = max(map(lambda x: len(x["uri"]) if isinstance(x, dict) else 0, obj)) \
            if obj else 0
        for item in obj:
            if isinstance(item, (str, int, float)):
                yield "\t{}".format(item)
            elif isinstance(item, dict):
                yield cls.formatter.format(
                    "{indent}{uri:+{uri_length}}\t# {info}",
                    **item, uri_length=uri_len, indent=indent)

    def _emit(self) -> Generator:
        if isinstance(self._data, dict):
            key_length = max(map(len, self._data.keys())) + 1
            for k, v in self._data.items():
                value = None
                if isinstance(v, (str, int, float)):
                    value = v
                elif isinstance(v, dict):
                    value = "{uri}\t# {info}".format(**v)
                if value:
                    yield "{k:{key_length}}\t{value}".format(k=k + ":", value=value,
                                                            key_length=key_length)
            for k, v in self._data.items():
                if isinstance(v, list):
                    yield "{}::".format(k)
                    yield from self._list_g(v, indent="\t")
        elif isinstance(self._data, list):
            yield from self._list_g(self._data)

    def emit(self) -> str:
        return "\n".join(self._emit())


class Dumper:
    _serializer: Type[Serializer] = None
    _emitter: Type[Emitter] = None
    _data: Union[BaseModel, RenderNode, list, str, dict]

    def __init__(self, data: Union[BaseModel, RenderNode, list, str, dict]):
        if isinstance(data, BaseModel):
            self._data = RenderNode(data, brief=False)
        else:
            self._data = data

    def dump(self):
        if isinstance(self._data, str):
            return self._data
        serialized = self._serializer(self._data).serialize()
        return self._emitter(serialized).emit()


class JsonDumper(Dumper):
    _serializer = JsonSerializer
    _emitter = JsonEmitter


class PlainDumper(Dumper):
    _serializer = PlainSerializer
    _emitter = PlainEmitter


def get_dumper(dumper_type: str) -> Type[Dumper]:
    if dumper_type == "json":
        return JsonDumper
    elif dumper_type == "plain":
        return PlainDumper
    else:
        raise ValueError


def show_song(song, uri_length=None, brief=False, fetch=False):
    """以一行文字的方式显示一首歌的信息

    :param uri_length: 控制 song uri 的长度
    :param brief: 是否只显示简要信息
    :param fetch: 是否在线请求未初始化的属性
    """
    artists_name = song.artists_name if fetch else song.artists_name_display
    song_title = song.title if fetch else song.title_display
    title = _fit_text(song_title or '', 18, filling=False)
    album_name = song.album_name if fetch else song.album_name_display

    song_uri = reverse(song)
    if uri_length is not None:
        song_uri = _fit_text(song_uri, uri_length)

    if brief:
        artists_name = _fit_text(artists_name, 20, filling=False)
        s = '{song}\t# {title} - {artists_name}'.format(
            song=song_uri,
            title=title,
            artists_name=artists_name)
        return s

    # XXX: 这个操作可能会产生网络请求
    album_uri = reverse(song.album)
    artists_uri = ','.join(reverse(artist) for artist in song.artists)
    msgs = (
        'provider:     {}'.format(song.source),
        '     uri:     {}'.format(song_uri),
        '   title:     {}'.format(song.title),
        'duration:     {}'.format(song.duration),
        '     url:     {}'.format(song.url),
        ' artists:     {}\t# {}'.format(artists_uri, artists_name),
        '   album:     {}\t# {}'.format(album_uri, album_name),
    )
    return '\n'.join(msgs)


def show_songs(songs):
    uri_length = max((len(reverse(song)) for song in songs)) if songs else None
    return '\n'.join([show_song(song, uri_length=uri_length, brief=True)
                      for song in songs])


def show_artist(artist, brief=False):
    if brief:
        return '{uri}\t# {name}'.format(
            uri=reverse(artist),
            name=artist.name)
    msgs = [
        'provider:      {}'.format(artist.source),
        'identifier:    {}'.format(artist.identifier),
        'name:          {}'.format(artist.name),
    ]
    if artist.songs:
        songs_header = ['songs::']
        songs = ['\t' + each for each in show_songs(artist.songs).split('\n')]
        msgs += songs_header
        msgs += songs
    return '\n'.join(msgs)


def show_album(album, brief=False):
    if brief:
        return '{uri}\t# {name} - {artists_name}'.format(
            uri=reverse(album),
            name=album.name,
            artists_name=album.artists_name
        )

    msgs = [
        'provider:      {}'.format(album.source),
        'identifier:    {}'.format(album.identifier),
        'name:          {}'.format(album.name),
    ]
    if album.artists is not None:
        artists = album.artists
        artists_id = ','.join([str(artist.identifier) for artist in artists])
        artists_name = ','.join([artist.name for artist in artists])
        msgs_artists = ['artists:       {}\t#{}'.format(artists_id, artists_name)]
        msgs += msgs_artists
    msgs_songs_header = ['songs::']
    msgs_songs = ['\t' + each for each in show_songs(album.songs).split('\n')]
    msgs += msgs_songs_header
    msgs += msgs_songs
    return '\n'.join(msgs)


def show_playlist(playlist, brief=False):
    if brief:
        content = '{playlist}\t#{name}'.format(
            playlist=playlist,
            name=playlist.name)
    else:
        parts = [
            'name:        {}'.format(playlist.name),
            'songs::',
        ]
        parts += ['\t' + show_song(song, brief=True) for song in playlist.songs]
        content = '\n'.join(parts)
    return content


def show_playlists(playlists):
    return '\n'.join((show_playlist(playlist, brief=True)
                      for playlist in playlists))


def show_user(user):
    parts = [
        'name:        {}'.format(user.name),
        'playlists::',
    ]
    parts += ['\t' + show_playlist(p, brief=True) for p in user.playlists]
    return '\n'.join(parts)


def show_search(search):
    """show search result model"""

    song_part = map(lambda so: show_song(so, brief=True),
                    search.songs or [])
    pl_part = map(lambda pl: show_playlist(pl, brief=True),
                  search.playlists or [])
    ar_part = map(lambda ar: show_artist(ar, brief=True),
                  search.artists or [])
    al_part = map(lambda al: show_album(al, brief=True),
                  search.albums or [])
    return '\n'.join(chain(song_part, ar_part, al_part, pl_part))
