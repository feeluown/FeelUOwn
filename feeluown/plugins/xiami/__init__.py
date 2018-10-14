# -*- coding: utf-8 -*-

import json
import logging
import os

from fuocore.xiami.provider import provider
from fuocore.xiami.models import XUserModel

from feeluown.consts import DATA_DIR

__alias__ = '虾米音乐'
__version__ = '0.1a1'
__desc__ = '虾米音乐'

logger = logging.getLogger(__name__)
USER_INFO_FILE = DATA_DIR + '/xiami_user_info.json'


def dump_user(user):
    assert user.access_token is not None
    data = {
        'id': user.identifier,
        'name': user.name,
        'access_token': user.access_token,
    }
    with open(USER_INFO_FILE, 'w') as f:
        json.dump(data, f)


def load_user():
    if not os.path.exists(USER_INFO_FILE):
        return None
    with open(USER_INFO_FILE) as f:
        user_data = json.load(f)
    user = XUserModel(source=provider.identifier,
                      identifier=user_data['id'],
                      name=user_data['name'],
                      access_token=user_data['access_token'])
    return user


class Xiami(object):
    """GUI 控制"""

    def __init__(self, app):
        from feeluown.components.provider import ProviderModel

        self._app = app
        self._user = None

        self._pm = ProviderModel(
            name='虾米音乐',
            desc='',
            on_click=self.show_provider)
        self._app.providers.assoc(provider.identifier, self._pm)

    def show_login_dialog(self):
        from .ui import LoginDialog
        dialog = LoginDialog()
        dialog.login_success.connect(self.bind_user)
        dialog.exec()

    def bind_user(self, user, dump=True):
        if dump:
            dump_user(user)
        self._user = user
        provider.auth(user)

    def show_provider(self):
        """展示虾米首页

        要求用户已经登录，支持展示用户名、用户歌单列表

        TODO: 可以考虑支持展示榜单等
        """
        from feeluown.components.my_music import MyMusicItem

        if self._user is None:
            user = load_user()
            if user is None:
                self.show_login_dialog()
            else:
                self.bind_user(user, dump=False)
        if self._user is not None:
            # 显示用户名
            self._pm.name = '虾米音乐 - {}'.format(self._user.name)
            # 显示播放列表/歌单
            self._app.playlists.clear()
            self._app.playlists.add(self._user.playlists)
            self._app.playlists.add(self._user.fav_playlists, is_fav=True)
            # 显示用户收藏的歌曲
            self._app.ui.left_panel.my_music_con.show()
            self._app.ui.left_panel.playlists_con.show()
            self._app.my_music.clear()
            def func():
                self._app.ui.table_container.show_songs(self._user.fav_songs)
            self._app.my_music.add(MyMusicItem(
                '♥ 我的收藏', on_click=func))


def enable(app):
    app.library.register(provider)
    if app.mode & app.GuiMode:
        Xiami(app)


def disable(app):
    app.library.deregister(provider)
