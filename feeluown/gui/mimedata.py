from PyQt5.QtCore import QMimeData

from feeluown.models import ModelType

from feeluown.gui.helpers import get_model_type


model_mimetype_map = {
    ModelType.dummy.value: 'fuo-model/x-dummy',
    ModelType.song.value: 'fuo-model/x-song',
    ModelType.playlist.value: 'fuo-model/x-playlist',
    ModelType.album.value: 'fuo-model/x-album',
    ModelType.artist.value: 'fuo-model/x-artist',
    ModelType.lyric.value: 'fuo-model/x-lyric',
    ModelType.user.value: 'fuo-model/x-user',
}


def get_model_mimetype(model):
    return model_mimetype_map[get_model_type(model)]


class ModelMimeData(QMimeData):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self._mimetype = get_model_mimetype(model)

    def setData(self, format, model):
        self._model = model

    def formats(self):
        return [self._mimetype]

    def hasFormat(self, format):
        return format == self._mimetype

    def data(self, format):
        if format == self._mimetype:
            return self.model
        return None
