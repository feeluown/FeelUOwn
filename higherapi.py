# -*- coding=utf8 -*-
__author__ = 'cosven'

from api import NetEase


class User(object):
    def __init__(self):
        self.netease = NetEase()
        self.is_login = False
        self.uid = str()    # ''

    def login(self, username, password):
        data = self.netease.login(username, password)
        code = data['code']
        if code is 200:
            self.uid = data['profile']['userId']
            self.is_login = True
            return True
        else:   # 501
            return False

    def get_favorite_playlist_id(self):
        """
        login required
        success: return playlist id
        fail: return empty string ''
        """
        if self.is_login:
            playlist = self.netease.user_playlist(self.uid)
            for each in playlist:
                if each['specialType'] is 5:    # favorite playlist
                    return each['id']   # the favorite playlist id
            return ''
        return ''

    def get_music_title_and_url(self, pid):
        """
        :param pid: playlist id
        :return re: return list re
        """
        playlist = self.netease.playlist_detail(pid)
        re = list()
        if playlist is not []:
            for music in playlist:
                tmp = dict()
                tmp['title'] = music['name']
                tmp['url'] = music['mp3Url']
                re.append(tmp)
        return re

