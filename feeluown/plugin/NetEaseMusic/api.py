#!/usr/bin/env python
# encoding: UTF-8

"""
网易云音乐 Api
https://github.com/bluetomlee/NetEase-MusicBox
The MIT License (MIT)
CopyRight (c) 2014 vellow <i@vellow.net>

modified by
"""

import json
import requests

from PyQt5.QtCore import pyqtSignal, QObject

from feeluown.base.utils import singleton, show_requests_progress
from feeluown.base.logger import LOG


uri = 'http://music.163.com/api'


@singleton
class NetEase(QObject):

    signal_load_progress = pyqtSignal([int])

    def __init__(self, headers=None, cookies=None):
        super().__init__()
        self.headers = headers
        self.cookies = cookies

    def http_request(self, method, action, query=None, urlencoded=None, callback=None, timeout=3):
        LOG.info('method=%s url=%s query=%s' % (method, action, query))
        try:
            res = None
            if method == "GET":
                res = requests.get(action, headers=self.headers, cookies=self.cookies, timeout=timeout)
            elif method == "POST":
                res = requests.post(action, data=query, headers=self.headers, cookies=self.cookies, timeout=timeout)
            elif method == "POST_UPDATE":
                res = requests.post(action, data=query, headers=self.headers, cookies=self.cookies, timeout=timeout)
                self.cookies.update(res.cookies.get_dict())
            content = show_requests_progress(res, self.signal_load_progress)
            content_str = content.decode('utf-8')
            content_dict = json.loads(content_str)
            return content_dict
        except Exception as e:
            LOG.error(str(e))
            return {"code": 408}

    def load_cookies(self, cookies):
        self.cookies = cookies

    def login(self, username, pw_encrypt, phone=False):
        action = 'http://music.163.com/api/login/'
        phone_action = 'http://music.163.com/api/login/cellphone/'
        data = {
            'username': username,
            'password': pw_encrypt,
            'rememberLogin': 'true'
        }

        phone_data = {
            'phone': username,
            'password': pw_encrypt,
            'rememberLogin': 'true'
        }

        if phone is True:
            res_data = self.http_request("POST_UPDATE", phone_action, phone_data)
            return res_data
        else:
            res_data = self.http_request("POST_UPDATE", action, data)
            return res_data

    def check_cookies(self):
        url = "http://music.163.com/api/push/init"
        data = self.http_request("POST_UPDATE", url, {})
        if data['code'] == 200:
            return True
        return False

    def confirm_captcha(self, captcha_id, text):
        action = 'http://music.163.com/api/image/captcha/verify/hf?id=' + str(captcha_id) + '&captcha=' + str(text)
        data = self.http_request('GET', action)
        return data

    def get_captcha_url(self, captcha_id):
        action = 'http://music.163.com/captcha?id=' + str(captcha_id)
        return action

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=200):
        action = 'http://music.163.com/api/user/playlist/?offset=' + str(offset) + '&limit=' + str(
            limit) + '&uid=' + str(uid)
        res_data = self.http_request('GET', action)
        return res_data

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, s, stype=1, offset=0, total='true', limit=60):
        action = 'http://music.163.com/api/search/get'
        data = {
            's': s,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        return self.http_request('POST', action, data)

    def playlist_detail(self, playlist_id):
        action = 'http://music.163.com/api/playlist/detail?id=' + str(playlist_id) + '&offset=0&total=true&limit=1001'
        res_data = self.http_request('GET', action)
        return res_data

    def update_playlist_name(self, pid, name):
        url = 'http://music.163.com/api/playlist/update/name'
        data = {
            'id': pid,
            'name': name
        }
        res_data = self.http_request('POST', url, data)
        return res_data

    def new_playlist(self, uid, name='default'):
        url = 'http://music.163.com/api/playlist/create'
        data = {
            'uid': uid,
            'name': name
        }
        res_data = self.http_request('POST', url, data)
        return res_data

    def delete_playlist(self, pid):
        url = 'http://music.163.com/api/playlist/delete'
        data = {
            'id': pid,
            'pid': pid
        }
        return self.http_request('POST', url, data)

    def artist_infos(self, artist_id):
        """
        :param artist_id: artist_id
        :return: {
            code: int,
            artist: {artist},
            more: boolean,
            hotSongs: [songs]
        }
        """
        action = 'http://music.163.com/api/artist/' + str(artist_id)
        data = self.http_request('GET', action)
        return data

    # album id --> song id set
    def album_infos(self, album_id):
        """
        :param album_id:
        :return: {
            code: int,
            album: { album }
        }
        """
        action = 'http://music.163.com/api/album/' + str(album_id)
        data = self.http_request('GET', action)
        return data

    # song id --> song url ( details )
    def song_detail(self, music_id):
        action = "http://music.163.com/api/song/detail/?id=" + str(music_id) + "&ids=[" + str(music_id) + "]"
        data = self.http_request('GET', action)
        return data

    # DJchannel ( id, channel_name ) ids --> song urls ( details )
    # 将 channels 整理为 songs 类型
    def channel_detail(self, channelids, offset=0):
        channels = []
        for i in range(0, len(channelids)):
            action = 'http://music.163.com/api/dj/program/detail?id=' + str(channelids[i])
            data = self.http_request('GET', action)
            try:
                channel = self.dig_info(data['program']['mainSong'], 'channels')
                channels.append(channel)
            except:
                continue

        return channels

    def add_music_to_playlist(self, mid, pid, op):
        """
        :param op: add or del
        把mid这首音乐加入pid这个歌单列表当中去
        1. 如果歌曲已经在列表当中，返回code为502
        """
        url_add = 'http://music.163.com/api/playlist/manipulate/tracks'
        trackIds = '["' + str(mid) + '"]'
        data_add = {
            'tracks': str(mid),  # music id
            'pid': str(pid),    # playlist id
            'trackIds': trackIds,  # music id str
            'op': op   # opation
        }
        return self.http_request('POST', url_add, data_add)

    def set_music_favorite(self, mid, flag):
        url = "http://music.163.com/api/song/like"
        data = {
            "trackId": mid,
            "like": str(flag).lower(),
            "time": 0
        }
        return self.http_request("POST", url, data)

    def get_radio_music(self):
        url = 'http://music.163.com/api/radio/get'
        return self.http_request('GET', url)

    def get_mv_detail(self, mvid):
        """Get mv detail
        :param mvid: mv id
        :return:
        """
        url = 'http://music.163.com/api/mv/detail?id=' + str(mvid)
        return self.http_request('GET', url)

    def get_lyric_by_musicid(self, mid):
        """Get song lyric
        :param mid: music id
        :return: {
            lrc: {
                version: int,
                lyric: str
            },
            tlyric: {
                version: int,
                lyric: str
            }
            sgc: bool,
            qfy: bool,
            sfy: bool,
            transUser: {},
            code: int,
        }
        """
        # tv 表示翻译。-1：表示要翻译，1：不要
        url = 'http://music.163.com/api/song/lyric?' + 'id=' + str(mid) + '&lv=1&kv=1&tv=-1'
        return self.http_request('GET', url)

    def get_similar_song(self, mid, offset=0, limit=10):
        url = ("http://music.163.com/api/discovery/simiSong"
               "?songid=%d&offset=%d&total=true&limit=%d"
               % (mid, offset, limit))
        return self.http_request('GET', url)

    def get_recommend_songs(self):
        url = 'http://music.163.com/api/discovery/recommend/songs'
        return self.http_request('GET', url)
