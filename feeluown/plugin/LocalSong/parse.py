# -*- coding: utf-8 -*-

import os

import mutagen

from .models import LocalSongModel


class Parser(object):
    def __init__(self):
        self._supported_suffix = ['.mp3', '.wav']
        pass

    def scan(self, path, depth=2):
        song_paths = []
        for song in os.listdir(path):
            song_path = os.path.join(path, song)
            if os.path.isdir(song_path) and depth > 0:
                song_paths.extend(self.scan(song_path, depth-1))
            elif os.path.splitext(song)[1] in self._supported_suffix:
                song_paths.append(song_path)
        return song_paths

    def analysis(self, song_path):
        song = mutagen.File(song_path)

        title = song['TIT2'].text[0] if 'TIT2' in song.keys() else 'Unknown'
        album = song['TALB'].text[0] if 'TALB' in song.keys() else 'Unknown'
        artist = song['TPE1'].text[0] if 'TPE1' in song.keys() else 'Unknown'
        length = song.info.length

        return LocalSongModel({'title': title,
                               'album': album,
                               'artist': artist,
                               'length': length,
                               'url': song_path})
