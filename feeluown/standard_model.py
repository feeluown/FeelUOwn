# -*- coding: utf-8 -*-


class SongModel(object):
    def __init__(self):
        pass

    def get_title(self):
        raise NotImplementedError('This should be implemented by subclass')

    def get_artists_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    def get_album_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    def get_url(self):
        raise NotImplementedError('This should be implemented by subclass')

    def get_length(self):
        raise NotImplementedError('This should be implemented by subclass')


class MvModel(object):
    def __init__(self):
        pass

    def get_related_song_model(self):
        return None

    def get_url(self):
        raise NotImplementedError('This should be implemented by subclass')


class ArtistModel(object):
    def __init__(self):
        pass

    def get_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    def get_albums(self):
        return []

    def get_songs(self):
        return []


class AlbumModel(object):
    def __init__(self):
        pass

    def get_name(object):
        raise NotImplementedError('This should be implemented by subclass')

    def get_img_url(object):
        raise NotImplementedError('This should be implemented by subclass')
