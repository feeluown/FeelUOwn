from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

from feeluown.library import (
    resolve, reverse, BriefSongModel, BriefPlaylistModel,
    SupportsPlaylistSongsReader,
)
from .base import AbstractHandler
from .excs import HandlerException


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

    def handle(self, cmd):  # pylint: disable=inconsistent-return-statements
        # pylint: disable=no-else-return
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

    def play(self, s):  # pylint: disable=inconsistent-return-statements
        # pylint: disable=no-else-return,too-many-branches
        if s.startswith('fuo://'):
            model = resolve(s)
            if model is None:
                return 'Invalid fuo uri.'
            elif isinstance(model, BriefSongModel):
                self._app.playlist.play_model(model)
            elif isinstance(model, BriefPlaylistModel):
                provider = self._app.library.get(model.source)
                if isinstance(provider, SupportsPlaylistSongsReader):
                    reader = provider.playlist_create_songs_rd(model)
                    songs = reader.readall()
                    self._app.playlist.set_models(songs, next_=True)
                    self._app.player.resume()
                else:
                    raise HandlerException(
                        f"provider:{provider.identifier} does not support"
                        " SupportsPlaylistSongsReader"
                    )
            else:
                model_type = model.meta.model_type
                raise HandlerException(f"can't play this model type: {model_type}")

            return
        elif s.startswith('http'):
            return self.player.play(s, video=False)

        # 取每个提供方的第一个搜索结果
        source_song_map: Any = defaultdict()
        for result in self.library.search(s):
            for song in result.songs:
                if song.source in source_song_map:
                    break
                source_song_map[song.source] = song
        songs = list(source_song_map.values())

        if songs:
            songs = sorted(songs, key=lambda song: score(s, repr_song(song)),
                           reverse=True)
            msg = f'select:\t{reverse(songs[0], as_line=True)}\n'
            self.playlist.play_model(songs[0])
            lines = []
            for song in songs[1:]:
                lines.append('\t' + reverse(song, as_line=True))
            if lines:
                msg += 'options::\n' + '\n'.join(lines)
            return msg
        else:
            return 'No song has been found.'
