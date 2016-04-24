from .api import Api
from .model import NSongModel, NAlbumModel, NArtistModel


class Normalize(object):
    def __init__(self):
        self._api = Api()

    def song_detail(self, mid):
        data = self._api.song_detail(mid)
        model = NSongModel.create(data)
        return model

    def album_detail(self, bid):
        data = self._api.album_infos(bid)
        model = NAlbumModel.create(data)
        return model

    def artist_detail(self, aid):
        data = self._api.artist_infos(aid)
        model = NArtistModel.create(data)
        return model
