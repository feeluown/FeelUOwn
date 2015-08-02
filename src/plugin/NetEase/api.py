#!/usr/bin/env python
# encoding: UTF-8

"""
网易云音乐 Api
https://github.com/bluetomlee/NetEase-MusicBox
The MIT License (MIT)
CopyRight (c) 2014 vellow <i@vellow.net>

modified by
"""

import re
import json
import hashlib

from base.common import singleton
from base.web import MyWeb
from base.logger import LOG

# list去重
def uniq(arr):
    arr2 = list(set(arr))
    arr2.sort(key=arr.index)
    return arr2

default_timeout = 10


@singleton
class NetEase:
    def __init__(self):
        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
        }
        self.cookies = {
            'appver': '1.5.2'
        }
        self.web = MyWeb()

    def http_request(self, method, action, query=None, urlencoded=None, callback=None, timeout=None):
        if method == 'GET':
            res = self.web.get(action)

        elif method == 'POST':
            res = self.web.post(action, query)

        try:
            # data = res.read()

            data = res.decode('utf-8')
            data = json.loads(data)
        except Exception as e:
            LOG.info(str(e))
            data = res
        return data

    # 登录
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
            res_data = self.http_request('POST', phone_action, phone_data)
            return res_data
        else:
            res_data = self.http_request('POST', action, data)
            return res_data

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
