#!/usr/bin/env python
# encoding: UTF-8

"""
网易云音乐 Api
https://github.com/bluetomlee/NetEase-MusicBox
The MIT License (MIT)
CopyRight (c) 2014 vellow <i@vellow.net>

modified by cosven
"""

import base64
import binascii
import os
import json
import logging
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
import requests
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA


site_uri = 'http://music.163.com'
uri = 'http://music.163.com/api'
uri_we = 'http://music.163.com/weapi'
uri_v1 = 'http://music.163.com/weapi/v1'

logger = logging.getLogger(__name__)



class Xiami(object):
    '''
    refrence: https://github.com/listen1/listen1
    '''
    def __init__(self):
        self._headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'api.xiami.com',
            'Referer': 'http://m.xiami.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2)'\
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome'\
                          '/33.0.1750.152 Safari/537.36',
        }
        pass

    def search(self, keyword):
        search_url = 'http://api.xiami.com/web?v=2.0&app_key=1&key={0}'\
                     '&page=1&limit=50&_ksTS=1459930568781_153&callback=jsonp154'\
                     '&r=search/songs'.format(keyword)
        try:
            res = requests.get(search_url, headers=self._headers)
            json_string = res.content[9:-1]
            data = json.loads(json_string.decode('utf-8'))
            return data['data'].get('songs')
        except Exception as e:
            logger.error(str(e))
        return []



class Api(object):
    def __init__(self):
        super().__init__()
        self.headers = {
            'Host': 'music.163.com',
            'Connection': 'keep-alive',
            'Referer': 'http://music.163.com/',
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/33.0.1750.152 Safari/537.36'
        }
        self._cookies = dict(appver="1.2.1", os="osx")
        self._http = None
        self.xiami_assister = Xiami()

    @property
    def cookies(self):
        return self._cookies

    def load_cookies(self, cookies):
        self._cookies.update(cookies)

    def set_http(self, http):
        self._http = http

    @property
    def http(self):
        return requests if self._http is None else self._http

    def request(self, method, action, query=None, timeout=3):
        # logger.info('method=%s url=%s data=%s' % (method, action, query))
        try:
            if method == "GET":
                res = self.http.get(action, headers=self.headers,
                                    cookies=self._cookies, timeout=timeout)
            elif method == "POST":
                res = self.http.post(action, data=query, headers=self.headers,
                                     cookies=self._cookies, timeout=timeout)
            elif method == "POST_UPDATE":
                res = self.http.post(action, data=query, headers=self.headers,
                                     cookies=self._cookies, timeout=timeout)
                self._cookies.update(res.cookies.get_dict())
            if res is not None:
                content = res.content
                content_str = content.decode('utf-8')
                content_dict = json.loads(content_str)
                return content_dict
            else:
                return None
        except Exception as e:
            logger.error(str(e))
            return None

    def login(self, username, pw_encrypt, phone=False):
        action = 'http://music.163.com/api/login/'
        phone_action = 'http://music.163.com/api/login/cellphone/'
        data = {
            'password': pw_encrypt,
            'rememberLogin': 'true'
        }
        if username.isdigit() and len(username) == 11:
            phone = True
            data.update({'phone': username})
        else:
            data.update({'username': username})
        if phone:
            res_data = self.request("POST_UPDATE", phone_action, data)
            return res_data
        else:
            res_data = self.request("POST_UPDATE", action, data)
            return res_data

    def check_cookies(self):
        url = uri + '/push/init'
        data = self.request("POST_UPDATE", url, {})
        if data['code'] == 200:
            return True
        return False

    def confirm_captcha(self, captcha_id, text):
        action = uri + '/image/captcha/verify/hf?id=' + str(captcha_id) +\
            '&captcha=' + str(text)
        data = self.request('GET', action)
        return data

    def get_captcha_url(self, captcha_id):
        action = 'http://music.163.com/captcha?id=' + str(captcha_id)
        return action

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=200):
        action = uri + '/user/playlist/?offset=' + str(offset) +\
            '&limit=' + str(limit) + '&uid=' + str(uid)
        res_data = self.request('GET', action)
        return res_data

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, s, stype=1, offset=0, total='true', limit=60):
        action = uri + '/search/get'
        data = {
            's': s,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        return self.request('POST', action, data)

    def playlist_detail(self, playlist_id):
        action = uri + '/playlist/detail?id=' + str(playlist_id) +\
            '&offset=0&total=true&limit=1001'
        res_data = self.request('GET', action)
        return res_data

    def update_playlist_name(self, pid, name):
        url = uri + '/playlist/update/name'
        data = {
            'id': pid,
            'name': name
        }
        res_data = self.request('POST', url, data)
        return res_data

    def new_playlist(self, uid, name='default'):
        url = uri + '/playlist/create'
        data = {
            'uid': uid,
            'name': name
        }
        res_data = self.request('POST', url, data)
        return res_data

    def delete_playlist(self, pid):
        url = uri + '/playlist/delete'
        data = {
            'id': pid,
            'pid': pid
        }
        return self.request('POST', url, data)

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
        action = uri + '/artist/' + str(artist_id)
        data = self.request('GET', action)
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
        action = uri + '/album/' + str(album_id)
        data = self.request('GET', action)
        return data

    def album_desc(self, album_id):
        action = site_uri + '/album'
        data = {'id': album_id}
        res = self.http.get(action, data)
        if res is None:
            return None
        soup = BeautifulSoup(res.content, 'html.parser')
        albdescs = soup.select('.n-albdesc')
        if albdescs:
            return albdescs[0].prettify()
        return ''

    def artist_desc(self, artist_id):
        action = site_uri + '/artist/desc'
        data = {'id': artist_id}
        res = self.http.get(action, data)
        if res is None:
            return None
        soup = BeautifulSoup(res.content, 'html.parser')
        artdescs = soup.select('.n-artdesc')
        if artdescs:
            return artdescs[0].prettify()
        return ''

    # song id --> song url ( details )
    def song_detail(self, music_id):
        action = uri + '/song/detail/?id=' + str(music_id) + '&ids=[' +\
            str(music_id) + ']'
        data = self.request('GET', action)
        return data

    def weapi_songs_url(self, music_ids, bitrate=320000):
        url = uri_we + '/song/enhance/player/url'
        data = {
            'ids': music_ids,
            'br': bitrate,
            'csrf_token': self._cookies.get('__csrf')
        }
        payload = self.encrypt_request(data)
        return self.request('POST', url, payload)

    def songs_detail(self, music_ids):
        music_ids = [str(music_id) for music_id in music_ids]
        action = uri + '/api/song/detail?ids=[' +\
            ','.join(music_ids) + ']'
        data = self.request('GET', action)
        return data

    def op_music_to_playlist(self, mid, pid, op):
        """
        :param op: add or del
        把mid这首音乐加入pid这个歌单列表当中去
        1. 如果歌曲已经在列表当中，返回code为502
        """
        url_add = uri + '/playlist/manipulate/tracks'
        trackIds = '["' + str(mid) + '"]'
        data_add = {
            'tracks': str(mid),  # music id
            'pid': str(pid),    # playlist id
            'trackIds': trackIds,  # music id str
            'op': op   # opation
        }
        return self.request('POST', url_add, data_add)

    def set_music_favorite(self, mid, flag):
        url = uri + '/song/like'
        data = {
            "trackId": mid,
            "like": str(flag).lower(),
            "time": 0
        }
        return self.request("POST", url, data)

    def get_radio_music(self):
        url = 'http://music.163.com/api/radio/get'
        return self.request('GET', url)

    def get_mv_detail(self, mvid):
        """Get mv detail
        :param mvid: mv id
        :return:
        """
        url = uri + '/mv/detail?id=' + str(mvid)
        return self.request('GET', url)

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
        url = uri + '/song/lyric?' + 'id=' + str(mid) + '&lv=1&kv=1&tv=-1'
        return self.request('GET', url)

    def get_similar_song(self, mid, offset=0, limit=10):
        url = ("http://music.163.com/api/discovery/simiSong"
               "?songid=%d&offset=%d&total=true&limit=%d"
               % (mid, offset, limit))
        return self.request('GET', url)

    def get_recommend_songs(self):
        url = uri + '/discovery/recommend/songs'
        return self.request('GET', url)

    def get_comment(self, comment_id):
        data = {
            'rid': comment_id,
            'offset': '0',
            'total': 'true',
            'limit': '20',
            'csrf_token': self._cookies.get('__csrf')
        }
        url = uri_v1 + '/resource/comments/' + comment_id
        payload = self.encrypt_request(data)
        return self.request('POST', url, payload)

    def accumulate_pl_count(self, mid):
        data = {"ids":"[%d]" % mid, "br":128000,
                "csrf_token": self._cookies.get('__scrf')}
        url = uri_we + '/pl/count'
        payload = self.encrypt_request(data)
        return self.request('POST', url, payload)

    def _create_aes_key(self, size):
        return (''.join([hex(b)[2:] for b in os.urandom(size)]))[0:16]

    def _aes_encrypt(self, text, key):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key, 2, '0102030405060708')
        enc_text = encryptor.encrypt(text)
        enc_text_encode = base64.b64encode(enc_text)
        return enc_text_encode

    def _rsa_encrypt(self, text):
        e = '010001'
        n = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615'\
            'bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf'\
            '695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46'\
            'bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b'\
            '8e289dc6935b3ece0462db0a22b8e7'
        reverse_text = text[::-1]
        pub_key = RSA.construct([int(n, 16), int(e, 16)])
        encrypt_text = pub_key.encrypt(int(binascii.hexlify(reverse_text), 16),
                                       None)[0]
        return format(encrypt_text, 'x').zfill(256)

    def encrypt_request(self, data):
        text = json.dumps(data)
        first_aes_key = '0CoJUm6Qyw8W8jud'
        second_aes_key = self._create_aes_key(16)
        enc_text = self._aes_encrypt(
            self._aes_encrypt(text, first_aes_key).decode('ascii'),
            second_aes_key).decode('ascii')
        enc_aes_key = self._rsa_encrypt(second_aes_key.encode('ascii'))
        payload = {
            'params': enc_text,
            'encSecKey': enc_aes_key,
        }
        return payload

    def get_xiami_song_by_title(self, title, artist_name):
        songs = self.xiami_assister.search(title)
        if not songs:
            return None

        target_song = songs[0]  # respect xiami search result
        max_match_ratio = 0.5
        for song in songs:
            if song['song_name'].lower() == title.lower():
                if song['artist_name'] == artist_name:
                    target_song = song
                    break
                ratio = SequenceMatcher(None, song['artist_name'], artist_name).ratio()
                if ratio > max_match_ratio:
                    max_match_ratio = ratio
                    target_song = song
        return target_song['listen_file']


api = Api()
