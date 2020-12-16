from collections import defaultdict
from difflib import SequenceMatcher

from feeluown.models.uri import resolve
from .base import AbstractHandler
from .helpers import show_song


def score(src, tar):
    s1 = int(SequenceMatcher(None, src, tar).ratio() * 50)
    s2 = 50
    delimiters = [' - ', '-', ' ']
    parts = []
    for delimiter in delimiters:
        if delimiter in src:
            parts = src.split(delimiter)
            break
    if parts:
        each_part_s = int(50 / len(parts))
        for part in parts:
            if part not in tar:
                s2 -= each_part_s
    return s1 + s2


def repr_song(song):
    return song.title + song.artists_name + song.album_name


class PlayerHandler(AbstractHandler):
    cmds = ('play', 'pause', 'stop', 'resume', 'toggle', )

    def handle(self, cmd):
        # TODO: 支持设置是否显示视频
        if cmd.action == 'play':
            s = ' '.join(cmd.args)
            return self.play(s)
        elif cmd.action == 'pause':
            # FIXME: please follow ``Law of Demeter``
            self.player.pause()
        elif cmd.action == 'stop':
            self.player.stop()
        elif cmd.action == 'resume':
            self.player.resume()
        elif cmd.action == 'toggle':
            self.player.toggle()

    def play(self, s):
        if s.startswith('fuo://'):
            song = resolve(s)
            if song is not None:
                self.player.play_song(song)
            return
        elif s.startswith('http'):
            return self.player.play(s, video=False)

        # 取每个提供方的第一个搜索结果
        source_song_map = defaultdict()
        for result in self.library.search(s):
            for song in result.songs:
                if song.source in source_song_map:
                    break
                source_song_map[song.source] = song
        songs = list(source_song_map.values())

        if songs:
            songs = sorted(songs, key=lambda song: score(s, repr_song(song)),
                           reverse=True)
            msg = 'select:\t{}\n'.format(show_song(songs[0], brief=True))
            self.player.play_song(songs[0])
            lines = []
            for song in songs[1:]:
                lines.append('\t' + show_song(song, brief=True))
            if lines:
                msg += 'options::\n' + '\n'.join(lines)
            return msg
        else:
            return 'No song has been found.'
