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
                raise TypeError('Please check your object type: ', key)

        return True

    def __getitem__(self, item):
        # 没有实现setitem， 暂时没用到这个函数，以后可能废弃
        if item in self.get_model():
            return self.get_model()[item]
        else:
            return None


class MusicModel(DataModel):
    """
    """
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'artists': list,
            'album': dict,
            'duration': int,
            'url': str
        }
        self.init_model()

class BriefMusicModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'artists': list,
            'album': dict,
            'duration': int,
        }
        self.init_model()


class ArtistModel(DataModel):
    """

    """
    def __init__(self, data, type=None):
        super().__init__(data, type=None)
        self._model = {
            'id': int,
            'name': str,
            'briefDesc': str
        }
        self.init_model()


class BriefArtistModel(DataModel):
    """

    """
    def __init__(self, data, type=None):
        super().__init__(data, type=None)
        self._model = {
            'id': int,
            'name': str,
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
            'tracks': list,
            'coverImgUrl': str,
            'type': int,  # 5 for favorite
            'uid': int
        }
        self.init_model()


class BriefPlaylistModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'coverImgUrl': str,
            'type': int,
            'uid': int
        }
        self.init_model()


class AlbumModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
            'briefDesc': str,
            'picUrl': str
        }
        self.init_model()


class BriefAlbumModel(DataModel):
    def __init__(self, data, type=None):
        super().__init__(data, type)
        self._model = {
            'id': int,
            'name': str,
        }
        self.init_model()



"""
url type: 指的就是这个url里面的内容是什么。比如说：是 验证码，是用户头像，是专辑图片，是音乐....
"""
url_type = ('captcha', 'album_img', 'avatar_img', )