class SongModel(object):
    def __init__(self):
        pass

    @property
    def mid(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def title(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def artists_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def album_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def album_img(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def url(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def length(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def source(self):
        raise NotImplementedError('This should be implemented by subclass')


class MvModel(object):
    def __init__(self):
        pass

    @property
    def song_model(self):
        return None

    @property
    def url(self):
        raise NotImplementedError('This should be implemented by subclass')


class ArtistModel(object):
    def __init__(self):
        pass

    @property
    def name(self):
        raise NotImplementedError('This should be implemented by subclass')


class AlbumModel(object):
    def __init__(self):
        pass

    @property
    def name(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def artists_name(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def img(self):
        return ''

    @property
    def songs(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def desc(self):
        return ''


class PlaylistModel(object):
    def __init__(self):
        pass

    @property
    def name(self):
        raise NotImplementedError('This should be implemented by subclass')

    @property
    def songs(self):
        raise NotImplementedError('This should be implemented by subclass')
