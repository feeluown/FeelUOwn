from collections import defaultdict
from difflib import SequenceMatcher
import json

from .base import AbstractHandler
from .helpers import show_song, get_url, ReturnMessage, ReturnStatus


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

    def handle(self, cmd, output_format):
        # TODO: 支持设置是否显示视频
        if cmd.action == 'play':
            s = ' '.join(cmd.args)
            return self.play(s, output_format)
        elif cmd.action == 'pause':
            # FIXME: please follow ``Law of Demeter``
            self.player.pause()
        elif cmd.action == 'stop':
            self.player.stop()
        elif cmd.action == 'resume':
            self.player.resume()
        elif cmd.action == 'toggle':
            self.player.toggle()

    def play(self, s, output_format):
        if s.startswith('fuo://'):
            song = self.model_parser.parse_line(s)
            if song is not None:
                self.player.play_song(song)
            if output_format == "plain":
                return
            elif output_format == "json":
                result = ReturnMessage(data={"type": "furi"}, output_format=output_format)
                return result.dumps()
        elif s.startswith('http'):
            if output_format == "plain":
                return self.player.play(s, video=False)
            else:
                data = {}
                data["type"] = "http"
                data["player"] = self.player.play(s, video=False)
                result = ReturnMessage(data=data, output_format=output_format)
                return result.dumps()


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
            self.player.play_song(songs[0])
            if output_format == "plain":
                msg = 'select:\t{}\n'.format(show_song(songs[0], brief=True))
                lines = []
                for song in songs[1:]:
                    lines.append('\t' + show_song(song, brief=True))
                if lines:
                    msg += 'options::\n' + '\n'.join(lines)
                return msg
            else:
                data = {}
                data["selected"] = get_url(songs[0])
                data["songs"] = list(map(get_url, songs))
                result = ReturnMessage(data=data, output_format=output_format)
                return result.dumps()
        else:
            if output_format == "plain":
                return 'No song has been found.'
            else:
                result = ReturnMessage(status=ReturnStatus.fail, data={"selected": "", "songs": []}, output_format=output_format)
                return result.dumps()
