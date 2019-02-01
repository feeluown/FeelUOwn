import json
from unittest.mock import patch
from unittest import TestCase

from fuocore.netease.api import API
from fuocore.netease.provider import provider
from fuocore.netease.models import NSongModel


with open('data/fixtures/netease/song.json') as f:
    data_song = json.load(f)['songs'][0]

with open('data/fixtures/netease/media.json') as f:
    data_media = json.load(f)

with open('data/fixtures/netease/album.json') as f:
    data_album = json.load(f)['album']

with open('data/fixtures/netease/artist.json') as f:
    data_artist = json.load(f)

with open('data/fixtures/netease/playlist.json') as f:
    data_playlist = json.load(f)

with open('data/fixtures/netease/search.json') as f:
    data_search = json.load(f)


class TestNeteaseModel(TestCase):
    def setUp(self):
        self.song = NSongModel(identifier=1,
                               title='dummy',
                               url=None,)

    @patch.object(API, 'songs_detail', return_value=[data_song])
    @patch.object(API, 'song_detail', return_value=data_song)
    def test_song_model(self, mock_song_detail, mock_songs_detail):
        song = provider.Song.get(-1)
        self.assertEqual(song.identifier, 29019227)
        songs = provider.Song.list([-1])
        self.assertEqual(songs[0].identifier, 29019227)

    @patch.object(API, 'get_lyric_by_songid', return_value={})
    @patch.object(API, 'song_detail', return_value=data_song)
    def test_song_lyric(self, mock_song_detail, mock_song_lyric):
        song = provider.Song.get(-1)
        self.assertEqual(song.lyric.content, '')
        self.assertTrue(mock_song_lyric.called)

    @patch.object(NSongModel, '_find_in_local', return_value='1.mp3')
    def test_song_url_1(self, mock_):
        """check if SongModel will find song in local first"""
        url = self.song.url
        self.assertEqual(url, '1.mp3')

    @patch.object(API, 'weapi_songs_url', return_value=data_media)
    @patch.object(NSongModel, '_find_in_local', return_value=None)
    def test_song_url_2(self, mock_find_in_local, mock_songs_url):
        """check if SongModel will refresh song url"""
        url = self.song.url
        self.assertEqual(url, data_media[0]['url'])

    @patch.object(API, 'album_desc', return_value='desc')
    @patch.object(API, 'album_infos', return_value=data_album)
    def test_album_model(self, mock_album_detail, mock_album_desc):
        album = provider.Album.get(-1)
        self.assertEqual(album.identifier, 2980029)
        self.assertEqual(album.desc, 'desc')
        self.assertTrue(mock_album_desc.called)
