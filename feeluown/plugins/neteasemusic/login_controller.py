import json
import logging
import os

from fuocore.netease.api import api
from fuocore.netease.schemas import NeteaseUserSchema

from .consts import USERS_INFO_FILE

logger = logging.getLogger(__name__)


def create_user(identifier, name, cookies):
    user, _ = NeteaseUserSchema(strict=True).load(dict(
        id=int(identifier),
        name=name,
        cookies=cookies,
    ))
    return user


class LoginController(object):
    _api = api

    def __init__(self, username, uid, name, img):
        super().__init__()
        self.username = username
        self.uid = uid
        self.name = name

    @classmethod
    def create(cls, data):
        user_data = data['data']
        # img = user_data['profile']['avatarUrl']
        uid = user_data['profile']['userId']
        name = user_data['profile']['nickname']
        user = create_user(uid, name, cls._api.cookies)
        return user

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

    @classmethod
    def save(cls, user):
        with open(USERS_INFO_FILE, 'w+') as f:
            data = {
                user.name: {
                    'uid': user.identifier,
                    'name': user.name,
                    'cookies': user.cookies
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
            uid = user_data['uid']
            name = user_data['name']
            cookies = user_data.get('cookies', cls._api.cookies)
            user = create_user(uid, name, cookies)
        return user
