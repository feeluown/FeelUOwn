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
from constants import DATA_PATH
from base.common import singleton, func_coroutine, write_json_into_file
from base.logger import LOG

# list去重
def uniq(arr):
    arr2 = list(set(arr))
    arr2.sort(key=arr.index)
    return arr2


"""
TODO: add local cache
"""

@singleton
class NetEase(QObject):

    signal_load_progress = pyqtSignal([int])
    cookies_filename = "netease_cookies.json"

    def __init__(self):
        super().__init__()
        self.headers = {
            'Host': 'music.163.com',
            'Connection': 'keep-alive',
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Referer': 'http://music.163.com/',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
        }
        self.cookies = dict(appver="1.2.1", os="osx")

    def show_progress(self, response):
        content = bytes()
        total_size = response.headers.get('content-length')
        if total_size is None:
            LOG.info(u'这个网络response没有Content-Length字段')
            content = response.content
            return content
        else:
            total_size = int(total_size)
            bytes_so_far = 0

            for chunk in response.iter_content():
                content += chunk
                bytes_so_far += len(chunk)
                progress = round(bytes_so_far * 1.0 / total_size * 100)
                self.signal_load_progress.emit(progress)
            return content

    def load_cookies(self):
        try:
            with open(DATA_PATH + self.cookies_filename) as f:
                data_str = f.read()
                self.cookies = json.loads(data_str)
        except Exception as e:
            LOG.error(str(e))

    @func_coroutine
    def save_cookies(self):
        try:
            write_json_into_file(self.cookies, DATA_PATH + self.cookies_filename)
            LOG.info("Save cookies successfully")
        except Exception as e:
            LOG.error(str(e))
            LOG.error("Save cookies failed")

    def http_request(self, method, action, query=None, urlencoded=None, callback=None, timeout=1):
        try:
            res = None
            if method == "GET":
                res = requests.get(action, headers=self.headers, cookies=self.cookies, timeout=timeout)
            elif method == "POST":
                res = requests.post(action, query, headers=self.headers, cookies=self.cookies, timeout=timeout)
            elif method == "POST_UPDATE":
                res = requests.post(action, query, headers=self.headers, cookies=self.cookies, timeout=timeout)
                self.cookies.update(res.cookies.get_dict())
                self.save_cookies()
            content = self.show_progress(res)
            content_str = content.decode('utf-8')
            content_dict = json.loads(content_str)
            return content_dict
        except Exception as e:
            LOG.error(str(e))
            return {"code": 408}

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
    def user_playlist(self, uid, offset=0, limit=100):
        action = 'http://music.163.com/api/user/playlist/?offset=' + str(offset) + '&limit=' + str(
            limit) + '&uid=' + str(uid)
        res_data = self.http_request('GET', action)
        return res_data

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, s, stype=1, offset=0, total='true', limit=60):
        action = 'http://music.163.com/api/search/get/web'
        data = {
            's': s,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        return self.http_request('POST', action, data)

    # 歌单详情
    def playlist_detail(self, playlist_id):
        action = 'http://music.163.com/api/playlist/detail?id=' + str(playlist_id) + '&offset=0&total=true&limit=1001'
        res_data = self.http_request('GET', action)
        return res_data

    # 歌手相关
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

    def addMusicToPlaylist(self, mid, pid, op):
        """
        :param op: add or del
        把mid这首音乐加入pid这个歌单列表当中去
        1. 如果歌曲已经在列表当中，返回code为502
        """
        url_add = 'http://music.163.com/api/playlist/manipulate/tracks'
        trackIds = '["' + str(mid) + '"]' 
        data_add = {
            'tracks': str(mid), # music id
            'pid': str(pid),    # playlist id
            'trackIds': trackIds, # music id str
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

    def getRadioMusic(self):
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
