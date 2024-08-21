"""
serializers for feeluown objects

TODO: too much code to define serializers for an object.
"""

from feeluown.app import App
from feeluown.library import AbstractProvider, SimpleSearchResult, reverse
from feeluown.player import PlaybackMode, State, Metadata
from . import PlainSerializer, PythonSerializer, \
    SerializerMeta, SimpleSerializerMixin
from .python import ListSerializer as PythonListSerializer
from .plain import ListSerializer as PlainListSerializer


class SearchSerializerMixin:
    """

    .. note::

        SearchModel isn't a standard model, it does not have identifier,
        the uri of SearchModel instance is also not so graceful, so we handle
        it as a normal object temporarily.
    """

    class Meta:
        types = (SimpleSearchResult,)

    def _get_items(self, result):
        fields = ('songs', 'albums', 'artists', 'playlists',)
        items = []
        for field in fields:
            value = getattr(result, field)
            if value:  # only append if it is not empty
                items.append((field, value))
        return items


class ProviderSerializerMixin:
    class Meta:
        types = (AbstractProvider,)

    def _get_items(self, provider):
        """
        :type provider: AbstractProvider
        """
        return [
            ('identifier', provider.identifier),
            ('uri', 'fuo://{}'.format(provider.identifier)),
            ('name', provider.name),
        ]


class AppSerializerMixin:
    class Meta:
        types = (App,)

    def _get_items(self, app):
        player = app.player
        playlist = app.playlist
        live_lyric = app.live_lyric

        repeat = playlist.playback_mode in (PlaybackMode.one_loop, PlaybackMode.loop)
        random = playlist.playback_mode == PlaybackMode.random
        items = [
            ('repeat', repeat),
            ('random', random),
            ('volume', player.volume),
            ('state', player.state.name),
        ]
        if player.state in (State.playing, State.paused) and \
                player.current_song is not None:
            items.extend([
                ('duration', player.duration),
                ('position', player.position),
                ('song', player.current_song),
                ('lyric-s', live_lyric.current_sentence),
            ])
        return items


class DictLikeSerializerMixin:
    class Meta:
        types = (Metadata,)

    def _get_items(self, metadata):
        return [(key.value, value) for key, value in metadata.items()]


# Python serializers.
#
class AppPythonSerializer(PythonSerializer,
                          AppSerializerMixin,
                          SimpleSerializerMixin,
                          metaclass=SerializerMeta):
    pass


class DictLikePythonSerializer(PythonSerializer,
                               DictLikeSerializerMixin,
                               SimpleSerializerMixin,
                               metaclass=SerializerMeta):
    pass


class ProviderPythonSerializer(PythonSerializer,
                               SimpleSerializerMixin,
                               ProviderSerializerMixin,
                               metaclass=SerializerMeta):
    pass


class SearchPythonSerializer(PythonSerializer, SearchSerializerMixin,
                             metaclass=SerializerMeta):

    def serialize(self, result):
        list_serializer = PythonListSerializer()
        json_ = {}
        for field, value in self._get_items(result):
            json_[field] = list_serializer.serialize(value)
        return json_


# Plain serializers.
#
class AppPlainSerializer(PlainSerializer,
                         AppSerializerMixin,
                         SimpleSerializerMixin,
                         metaclass=SerializerMeta):
    ...


class ProviderPlainSerializer(PlainSerializer, ProviderSerializerMixin,
                              metaclass=SerializerMeta):

    def __init__(self, **options):
        super().__init__(**options)
        self.opt_as_line = options.get('as_line', False)
        self.opt_uri_length = options.get('uri_length', '')

    def serialize(self, provider):
        """
        :type provider: AbstractProvider
        """
        items = self._get_items(provider)
        dict_ = dict(items)
        uri = dict_['uri']
        name = dict_['name']
        if self.opt_as_line or self.opt_level > 0:
            return '{uri:{uri_length}}\t# {name}'.format(
                uri=uri,
                name=name,
                uri_length=self.opt_uri_length
            )
        return self.serialize_items(items)


class SearchPlainSerializer(PlainSerializer, SearchSerializerMixin,
                            metaclass=SerializerMeta):

    def __init__(self, **options):
        super().__init__(**options)
        self.opt_uri_length = options.get('uri_length', '')

    def serialize(self, result):
        items = self._get_items(result)
        # when serialize SearchModel, we formatt it as one line when level > 1
        if self.opt_level >= 2:
            return str(result)  # I think we will never use this line format
        text_list = []
        for field, value in items:
            serializer = PlainListSerializer(
                level=self.opt_level - 1,
                fetch=False,
                uri_length=self.opt_uri_length
            )
            value_text = serializer.serialize(value)
            text_list.append(value_text)
        return '\n'.join(text_list)

    def calc_max_uri_length(self, result):
        items = self._get_items(result)
        uri_length = 0
        for field, value in items:
            for each in value:
                uri_length = max(uri_length, len(reverse(each)))
        return uri_length
