from feeluown.models import ModelType
from feeluown.models.uri import resolve, reverse
from feeluown.utils.utils import to_readall_reader
from .base import AbstractHandler


class PlaylistHandler(AbstractHandler):
    cmds = ('add', 'remove', 'list', 'next', 'previous', 'clear',)

    def handle(self, cmd):
        if cmd.action == 'add':
            return self.add(cmd.args)
        elif cmd.action == 'remove':
            return self.remove(cmd.args[0].strip())
        elif cmd.action == 'clear':
            return self.clear()
        elif cmd.action == 'list':
            return self.list()
        elif cmd.action == 'next':
            self.playlist.next()
        elif cmd.action == 'previous':
            self.playlist.previous()

    def add(self, furi_list):
        playlist = self.playlist
        for furi in furi_list:
            furi = furi.strip()
            obj = resolve(furi)
            if obj is not None:
                obj_type = type(obj).meta.model_type
                if obj_type == ModelType.song:
                    playlist.add(obj)
                elif obj_type == ModelType.playlist:
                    songs = to_readall_reader(obj, "songs").readall()
                    for song in songs:
                        playlist.add(song)

    def remove(self, song_uri):
        # FIXME: a little bit tricky
        for song in self.playlist.list():
            if reverse(song) == song_uri:
                self.playlist.remove(song)
                break

    def list(self):
        songs = self.playlist.list()
        return songs

    def clear(self):
        self.playlist.clear()
