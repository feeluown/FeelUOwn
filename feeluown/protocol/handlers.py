import logging

from abc import ABC, abstractmethod
from collections import defaultdict
from urllib.parse import urlparse

from fuocore.player import PlaybackMode, State
from .helpers import show_songs, show_song, get_url
from .parser import ModelParser


logger = logging.getLogger(__name__)


class AbstractHandler(ABC):
    def __init__(self, app, live_lyric):
        self.app = app
        self.live_lyric = live_lyric
        self.model_parser = ModelParser(self.app.library)

    @abstractmethod
    def handle(self, cmd):
        pass


class SearchHandler(AbstractHandler):
    def handle(self, cmd):
        return self.search_songs(cmd.args[0])

    def search_songs(self, query):
        logger.debug('搜索 %s ...', query)
        providers = self.app.library.list()
        source_in = [provd.identifier for provd in providers
                     if provd.Song.meta.allow_get]
        songs = []
        for result in self.app.library.search(query, source_in=source_in):
            logger.debug('从 %s 搜索到 %d 首歌曲，取前 20 首',
                         result.source, len(result.songs))
            songs.extend(result.songs[:20])
        logger.debug('总共搜索到 %d 首歌曲', len(songs))
        return show_songs(songs)


class StatusHandler(AbstractHandler):
    def handle(self, cmd):
        player = self.app.player
        playlist = self.app.playlist
        live_lyric = self.live_lyric
        repeat = int(playlist.playback_mode in
                     (PlaybackMode.one_loop, PlaybackMode.loop))
        random = int(playlist.playback_mode == PlaybackMode.random)
        msgs = [
            'repeat:    {}'.format(repeat),
            'random:    {}'.format(random),
            'volume:    {}'.format(player.volume),
            'state:     {}'.format(player.state.name),
        ]
        if player.state in (State.paused, State.playing):
            msgs += [
                'duration:  {}'.format(player.duration),
                'position:  {}'.format(player.position),
                'song:      {}'.format(show_song(player.current_song, brief=True)),  # noqa
                'lyric-s:   {}'.format(live_lyric.current_sentence),
            ]
        return '\n'.join(msgs)


class PlayerHandler(AbstractHandler):
    def handle(self, cmd):
        if cmd.action == 'play':
            song_furi = cmd.args[0]
            return self.play_song(song_furi.strip())
        elif cmd.action == 'pause':
            # FIXME: please follow ``Law of Demeter``
            self.app.player.pause()
        elif cmd.action == 'stop':
            self.app.player.stop()
        elif cmd.action == 'resume':
            self.app.player.resume()
        elif cmd.action == 'toggle':
            self.app.player.toggle()

    def play_song(self, song_furi):
        song = self.model_parser.parse_line(song_furi)
        if song is not None:
            self.app.player.play_song(song)


class PlaylistHandler(AbstractHandler):
    def handle(self, cmd):
        if cmd.action == 'add':
            return self.add(cmd.args[0].strip())
        elif cmd.action == 'remove':
            return self.remove(cmd.args[0].strip())
        elif cmd.action == 'clear':
            return self.clear()
        elif cmd.action == 'list':
            return self.list()
        elif cmd.action == 'next':
            self.app.player.play_next()
        elif cmd.action == 'previous':
            self.app.player.play_previous()

    def add(self, furis):
        playlist = self.app.playlist
        furi_list = furis.split(',')
        for furi in furi_list:
            song = self.model_parser.parse_line(furi)
            playlist.add(song)

    def remove(self, song_uri):
        # FIXME: a little bit tricky
        for song in self.app.playlist.list():
            if get_url(song) == song_uri:
                self.app.playlist.remove(song)
                break

    def list(self):
        songs = self.app.playlist.list()
        return show_songs(songs)

    def clear(self):
        self.app.playlist.clear()


class HelpHandler(AbstractHandler):
    def handle(self, cmd):
        return """
Available commands::

    search <string>  # search songs by <string>
    show fuo://xxx  # show xxx detail info
    play fuo://xxx/songs/yyy  # play yyy song
    list  # show player current playlist
    status  # show player status
    next  # play next song
    previous  # play previous song
    pause
    resume
    toggle

Watch live lyric::

    echo "sub topic.live_lyric" | nc host 23334
"""
