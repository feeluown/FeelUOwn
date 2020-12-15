"""
serializers for feeluown objects
"""

from feeluown.player import PlaybackMode, State
from feeluown.app import App
from . import PlainSerializer, PythonSerializer, \
    SerializerMeta, SimpleSerializerMixin


__all__ = (
    'AppPythonSerializer',
    'AppPlainSerializer',
)


class AppSerializerMixin:
    class Meta:
        types = (App, )

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


class AppPythonSerializer(PythonSerializer,
                          AppSerializerMixin,
                          SimpleSerializerMixin,
                          metaclass=SerializerMeta):
    pass


class AppPlainSerializer(PlainSerializer,
                         AppSerializerMixin,
                         SimpleSerializerMixin,
                         metaclass=SerializerMeta):
    pass
