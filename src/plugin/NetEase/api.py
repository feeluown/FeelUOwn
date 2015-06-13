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

    def httpRequest(self, method, action, query=None, urlencoded=None, callback=None, timeout=None):
        if (method == 'GET'):
            res = self.web.get(action)

        elif (method == 'POST'):
            res = self.web.post(action, query)

        try:
            data = res.read()
            data = data.decode('utf-8')
            data = json.loads(data)
        except Exception as e:
            LOG.warning(str(e))
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

        if phone is True:
            return self.httpRequest('POST', phone_action, data)
        else:
            return self.httpRequest('POST', action, data)

    def confirm_captcha(self, id, text):
        action = 'http://music.163.com/api/image/captcha/verify/hf?id=' + str(id) + '&captcha=' + str(text)
        data = self.httpRequest('GET', action)
        return data

    def get_captcha_url(self, captcha_id):
        action = 'http://music.163.com/captcha?id=' + str(captcha_id)
        return action

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=100):
        action = 'http://music.163.com/api/user/playlist/?offset=' + str(offset) + '&limit=' + str(
            limit) + '&uid=' + str(uid)
        data = self.httpRequest('GET', action)

        return data['playlist']

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
        return self.httpRequest('POST', action, data)

    # 新碟上架 http://music.163.com/#/discover/album/
    def new_albums(self, offset=0, limit=50):
        action = 'http://music.163.com/api/album/new?area=ALL&offset=' + str(offset) + '&total=true&limit=' + str(limit)
        data = self.httpRequest('GET', action)
        return data['albums']

    # 歌单（网友精选碟） hot||new http://music.163.com/#/discover/playlist/
    def top_playlists(self, category='全部', order='hot', offset=0, limit=50):
        action = 'http://music.163.com/api/playlist/list?cat=' + category + '&order=' + order + '&offset=' + str(
            offset) + '&total=' + ('true' if offset else 'false') + '&limit=' + str(limit)
        data = self.httpRequest('GET', action)
        return data['playlists']

    # 歌单详情
    def playlist_detail(self, playlist_id):
        action = 'http://music.163.com/api/playlist/detail?id=' + str(playlist_id)
        data = self.httpRequest('GET', action)
        return data['result']

    # 热门歌手 http://music.163.com/#/discover/artist/
    def top_artists(self, offset=0, limit=100):
        action = 'http://music.163.com/api/artist/top?offset=' + str(offset) + '&total=false&limit=' + str(limit)
        data = self.httpRequest('GET', action)
        return data['artists']

    # 歌手单曲
    def artists(self, artist_id):
        action = 'http://music.163.com/api/artist/' + str(artist_id)
        data = self.httpRequest('GET', action)
        return data['hotSongs']

    # album id --> song id set
    def album(self, album_id):
        action = 'http://music.163.com/api/album/' + str(album_id)
        data = self.httpRequest('GET', action)
        return data['album']['songs']

    # song ids --> song urls ( details )
    def songs_detail(self, ids, offset=0):
        tmpids = ids[offset:]
        tmpids = tmpids[0:100]
        tmpids = map(str, tmpids)
        action = 'http://music.163.com/api/song/detail?ids=[' + (',').join(tmpids) + ']'
        data = self.httpRequest('GET', action)
        return data['songs']

    # song id --> song url ( details )
    def song_detail(self, music_id):
        action = "http://music.163.com/api/song/detail/?id=" + str(music_id) + "&ids=[" + str(music_id) + "]"
        data = self.httpRequest('GET', action)
        return data['songs']

    # DJchannel ( id, channel_name ) ids --> song urls ( details )
    # 将 channels 整理为 songs 类型
    def channel_detail(self, channelids, offset=0):
        channels = []
        for i in range(0, len(channelids)):
            action = 'http://music.163.com/api/dj/program/detail?id=' + str(channelids[i])
            data = self.httpRequest('GET', action)
            try:
                channel = self.dig_info(data['program']['mainSong'], 'channels')
                channels.append(channel)
            except:
                continue

        return channels

    def dig_info(self, data, dig_type):
        temp = []
        if dig_type == 'songs':
            for i in range(0, len(data)):
                song_info = {
                    'song_id': data[i]['id'],
                    'artist': [],
                    'song_name': data[i]['name'],
                    'album_name': data[i]['album']['name'],
                    'mp3_url': data[i]['mp3Url']
                }
                if 'artist' in data[i]:
                    song_info['artist'] = data[i]['artist']
                elif 'artists' in data[i]:
                    for j in range(0, len(data[i]['artists'])):
                        song_info['artist'].append(data[i]['artists'][j]['name'])
                    song_info['artist'] = ', '.join(song_info['artist'])
                else:
                    song_info['artist'] = '未知艺术家'

                temp.append(song_info)

        elif dig_type == 'artists':
            temp = []
            for i in range(0, len(data)):
                artists_info = {
                    'artist_id': data[i]['id'],
                    'artists_name': data[i]['name'],
                    'alias': ''.join(data[i]['alias'])
                }
                temp.append(artists_info)

            return temp

        elif dig_type == 'albums':
            for i in range(0, len(data)):
                albums_info = {
                    'album_id': data[i]['id'],
                    'albums_name': data[i]['name'],
                    'artists_name': data[i]['artist']['name']
                }
                temp.append(albums_info)

        elif dig_type == 'playlists':
            for i in range(0, len(data)):
                playlists_info = {
                    'playlist_id': data[i]['id'],
                    'playlists_name': data[i]['name'],
                    'creator_name': data[i]['creator']['nickname']
                }
                temp.append(playlists_info)


        elif dig_type == 'channels':
            channel_info = {
                'song_id': data['id'],
                'song_name': data['name'],
                'artist': data['artists'][0]['name'],
                'album_name': 'DJ节目',
                'mp3_url': data['mp3Url']
            }
            temp = channel_info

        return temp

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
        return self.httpRequest('POST', url_add, data_add)

    def getRadioMusic(self):
        url = 'http://music.163.com/api/radio/get'
        return self.httpRequest('GET', url)
