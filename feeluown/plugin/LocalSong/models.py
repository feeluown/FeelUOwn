# -*- coding: utf-8 -*-


from feeluown.standard_model import SongModel


class LocalSongModel(SongModel):
    def __init__(self, data):
        self._data = data

    def get_title(self):
        return self._data['title']

    def get_artists_name(self):
        return self._data['artist']

    def get_album_name(self):
        return self._data['album']

    def get_length(self):
        return self._data['length']

    def get_url(self):
        return self._data['url']
