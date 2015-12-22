# -*- coding:utf-8 -*-

from functools import partial

from PyQt5.QtWidgets import QPushButton, QMenu, QAction

from feeluown.controller_api import ControllerApi


class Add_to_playlist_btn(QPushButton):
    def __init__(self):
        super().__init__('+')
        self.setToolTip('添加到歌单')
        self.menu = QMenu()
        self.playlists = []

    def mousePressEvent(self, event):
        self.set_playlists_options()
        self.menu.exec(event.globalPos())

    def set_playlists_options(self):
        playlists = ControllerApi.api.get_user_playlist()
        if not ControllerApi.api.is_response_ok(playlists):
            return
        self.playlists = playlists
        self.menu.clear()
        for playlist in playlists:
            if ControllerApi.api.is_playlist_mine(playlist):
                name = playlist['name']
                pid = playlist['id']
                action = QAction(name, self)
                action.triggered.connect(partial(self.add_to_playlist, pid))
                self.menu.addAction(action)

    def add_to_playlist(self, pid):
        if not ControllerApi.state['current_mid']:
            return False
        flag = ControllerApi.api.add_song_to_playlist(ControllerApi.state['current_mid'], pid)
        if flag:
            ControllerApi.notify_widget.show_message('◕◡◔', '加入歌单成功')
        else:
            ControllerApi.notify_widget.show_message('◕◠◔', '加入歌单失败, 可能早已在列表了哦')
