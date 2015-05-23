# -*- coding:utf8 -*-

from base.logger import LOG


class DataModel(object):
    def __init__(self, data, type=None):
        super().__init__()
        self.type = type    # such as: douban, neteasemusic ... for different music plugin
        self.data_model = {}
        self._model = {}
        self.data = data

    def get_model_type(self):
        return self.type

    def get_model(self):
        return self.data_model

    def init_model(self):
        if self.validate() is True:
            for key in self._model:
                self.data_model[key] = self.data[key]

    def validate(self):
        """ check dict keys and data type
        :return:
        """
        for key in self._model:
            if key not in self.data:
                raise KeyError('data should have key: ' + key)

            if not isinstance(self.data[key], self._model[key]):
                raise TypeError('Please check your object type')

        return True


class MusicModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'artists': list,
            'album': dict,
            'duration': str,
            'mp3Url': str
        }
        self.init_model()


class UserModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'uid': int,
            'username': str,
            'avatar': str
        }
        self.init_model()


class PlaylistModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'songs': list
        }
        self.init_model()
