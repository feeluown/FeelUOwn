import logging
import json

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

api_base_url = 'http://c.y.qq.com'


class API(object):
    """qq music api

    Please http capture request from (mobile) qqmusic mobile web page
    """

    def __init__(self, timeout=1):
        # TODO: 暂时无脑统一一个 timeout
        # 正确的应该是允许不同接口有不同的超时时间
        self._timeout = timeout
        self._headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Referer': 'http://y.qq.com/',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/66.0.3359.181 Mobile Safari/537.36',
        }

    def get_cover(self, mid, type_):
        """获取专辑、歌手封面

        :param type_: 专辑： 2，歌手：1
        """
        return 'http://y.gtimg.cn/music/photo_new/T00{}R800x800M000{}.jpg' \
            .format(type_, mid)

    def get_song_detail(self, song_id):
        song_id = int(song_id)
        url = 'http://u.y.qq.com/cgi-bin/musicu.fcg'
        # 往 payload 添加字段，有可能还可以获取相似歌曲、歌单等
        payload = {
            "comm": {
                "g_tk":5381,
                "uin": 0,
                "format": "json",
                "inCharset": "utf-8",
                "outCharset": "utf-8",
                "notice": 0,
                "platform": "h5",
                "needNewCode": 1
            },
            "detail": {
                "module": "music.pf_song_detail_svr",
                "method": "get_song_detail",
                "param": {"song_id": song_id}
            }
        }
        payload_str = json.dumps(payload)
        response = requests.post(url, data=payload_str, headers=self._headers,
                                 timeout=self._timeout)
        data = response.json()
        data_song = data['detail']['data']['track_info']
        if data_song['id'] <= 0:
            return None
        return data_song

    def get_song_url(self, song_mid):
        url = 'http://i.y.qq.com/v8/playsong.html'
        params = {
            'songmid': song_mid,
            'ADTAG': 'myqq',
            'from': 'myqq',
            'channel': 10007100,
        }
        # FIXME: set timeout to 2s as the responseis time is quite long
        response = requests.get(url, params=params, headers=self._headers,
                                timeout=2)
        soup = BeautifulSoup(response.content, 'html.parser')
        media = soup.select('#h5audio_media')
        if media:
            return media[0].get('src')
        return None

    def search(self, keyword, limit=20, page=1):
        path = '/soso/fcgi-bin/client_search_cp'
        url = api_base_url + path
        params = {
            # w,n,page are required parameters
            'w': keyword,
            'n': limit,
            'page': page,

            # positional parameters
            'cr': 1,  # copyright?
        }
        response = requests.get(url, params=params, timeout=self._timeout)
        content = response.text[9:-1]
        songs = json.loads(content)['data']['song']['list']
        return songs

    def artist_detail(self, artist_id):
        """获取歌手详情"""
        path = '/v8/fcg-bin/fcg_v8_singer_track_cp.fcg'
        url = api_base_url + path
        params = {
            'singerid': artist_id,
            'songstatus': 1,
            'order': 'listen',
            'begin': 0,
            'num': 50,
            'from': 'h5',
            'platform': 'h5page',
        }
        resp = requests.get(url, params=params, timeout=self._timeout)
        rv = resp.json()
        return rv['data']

    def album_detail(self, album_id):
        url = api_base_url + '/v8/fcg-bin/fcg_v8_album_info_cp.fcg'
        params = {
            'albumid': album_id,
            'format': 'json'
        }
        resp = requests.get(url, params=params)
        return resp.json()['data']
