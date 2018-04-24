import json
import logging
import os

from fuocore.netease.api import api

from .consts import USERS_INFO_FILE

logger = logging.getLogger(__name__)


class NUserModel(object):
    _api = api
    current_user = None

    def __init__(self, username, uid, name, img, playlists=[]):
        super().__init__()
        self.username = username

        self.uid = uid
        self.name = name
        self.img = img
        self._playlists = playlists

    def is_playlist_mine(self, pid):
        for p in self.playlists:
            if p.pid == pid:
                return True
        return False

    @classmethod
    def set_current_user(cls, user):
        cls.current_user = user

    @classmethod
    def create(cls, data):
        user_data = data['data']
        username = data['username']
        img = user_data['profile']['avatarUrl']
        uid = user_data['profile']['userId']
        name = user_data['profile']['nickname']
        model = NUserModel(username, uid, name, img)
        return model

    @classmethod
    def check(cls, username, pw):
        data = cls._api.login(username, pw)
        if data is None:
            return {'code': 408, 'message': '网络状况不好'}
        elif data['code'] == 200:
            return {'code': 200, 'message': '登陆成功',
                    'data': data, 'username': username}
        elif data['code'] == 415:
            captcha_id = data['captchaId']
            url = cls._api.get_captcha_url(captcha_id)
            return {'code': 415, 'message': '本次登陆需要验证码',
                    'captcha_url': url, 'captchar_id': captcha_id}
        elif data['code'] == 501:
            return {'code': 501, 'message': '用户名不存在'}
        elif data['code'] == 502:
            return {'code': 502, 'message': '密码错误'}
        elif data['code'] == 509:
            return {'code': 509, 'message': '请休息几分钟再尝试'}

    @classmethod
    def check_captcha(cls, captcha_id, text):
        flag, cid = cls._api.confirm_captcha(captcha_id, text)
        if flag is not True:
            url = cls._api.get_captcha_url(cid)
            return {'code': 415, 'message': '验证码错误',
                    'captcha_url': url, 'captcha_id': cid}
        return {'code': 200, 'message': '验证码正确'}

    def save(self):
        with open(USERS_INFO_FILE, 'w+') as f:
            data = {
                self.username: {
                    'uid': self.uid,
                    'name': self.name,
                    'img': self.img,
                    'cookies': self._api.cookies
                }
            }
            if f.read() != '':
                data.update(json.load(f))
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls):
        if not os.path.exists(USERS_INFO_FILE):
            return None
        with open(USERS_INFO_FILE, 'r') as f:
            text = f.read()
            if text == '':
                return None
            data = json.loads(text)
            username = next(iter(data.keys()))
            user_data = data[username]
            model = cls(username,
                        user_data['uid'],
                        user_data['name'],
                        user_data['img'])
            model._api.load_cookies(user_data['cookies'])
        return model

    @classmethod
    def get_recommend_songs(cls):
        if cls.current_user is None:
            return []
        data = cls._api.get_recommend_songs()
        if data.get('code') == 200:
            return NSongModel.batch_create(data['recommend'])
        return []

    @classmethod
    def get_fm_song(cls):
        if cls.current_user is None:
            return []
        data = cls._api.get_radio_music()
        if data is None:
            return []
        if data['code'] == 200:
            songs = data['data']
            return NSongModel.batch_create(songs)
        else:
            return []
