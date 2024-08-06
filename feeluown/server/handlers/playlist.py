from feeluown.library import ModelType, SupportsPlaylistSongsReader
from feeluown.library import resolve, reverse
from .base import AbstractHandler


class PlaylistHandler(AbstractHandler):
    cmds = ('add', 'remove', 'list', 'next', 'previous', 'clear',)

    def handle(self, cmd):  # pylint: disable=inconsistent-return-statements
        # pylint: disable=no-else-return
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
                obj_type = obj.meta.model_type
                if obj_type == ModelType.song:
                    playlist.add(obj)
                elif obj_type == ModelType.playlist:
                    provider = self.library.get(obj.source)
                    if isinstance(provider, SupportsPlaylistSongsReader):
                        reader = provider.playlist_create_songs_rd(obj)
                        for song in reader:
                            playlist.add(song)
                    # TODO: raise error if it does not support

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
