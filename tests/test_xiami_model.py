import json
from unittest.mock import patch
from unittest import TestCase

from fuocore.xiami.api import API
from fuocore.xiami.provider import provider


with open('data/fixtures/xiami/song.json') as f:
    data_song = json.load(f)

with open('data/fixtures/xiami/album.json') as f:
    data_album = json.load(f)

with open('data/fixtures/xiami/artist.json') as f:
    data_artist = json.load(f)

with open('data/fixtures/xiami/artist_songs.json') as f:
    data_artist_songs = json.load(f)

with open('data/fixtures/xiami/playlist.json') as f:
    data_playlist = json.load(f)

with open('data/fixtures/xiami/user.json') as f:
    data_user = json.load(f)

with open('data/fixtures/xiami/user_playlists.json') as f:
    data_user_playlists = json.load(f)

with open('data/fixtures/xiami/search.json') as f:
    data_search = json.load(f)


class TestXiamiModel(TestCase):
    @patch.object(API, 'song_detail', return_value=data_song)
    def test_song_model(self, mock_song_detail):
        song = provider.Song.get(11)
        self.assertEqual(song.source, 'xiami')
        self.assertEqual(song.identifier, 1801370698)
        self.assertEqual(song.album.identifier, 2103467442)

    @patch.object(API, 'album_detail', return_value=data_album)
    def test_album_model(self, mock_album_detail):
        album = provider.Album.get(11)
        self.assertEqual(len(album.songs), 11)
        self.assertEqual(album.identifier, 2100387382)
        self.assertEqual(album.songs[0].artists[0].name, '范晓萱')
        self.assertTrue(album.desc)
        self.assertTrue(len(album.artists), 2)

    @patch.object(API, 'artist_detail', return_value=data_artist)
    @patch.object(API, 'album_detail', return_value=data_album)
    def test_artist_desc_field(self, mock_album_detail, mock_artist_detail):
        """album.artists[0].desc 不需要请求网络"""
        album = provider.Album.get(11)
        artist = album.artists[0]
        artist.desc
        self.assertFalse(mock_artist_detail.called)

    @patch.object(API, 'artist_detail', return_value=data_artist)
    @patch.object(API, 'song_detail', return_value=data_song)
    def test_artist_desc_field_2(self, mock_song_detail, mock_artist_detail):
        """song.artists[0].desc 需要请求网络"""
        song = provider.Song.get(11)
        artist = song.artists[0]
        artist.desc
        artist.desc
        mock_artist_detail.assert_called_once_with(artist.identifier)

    @patch.object(API, 'album_detail', return_value=data_album)
    @patch.object(API, 'song_detail', return_value=data_song)
    def test_album_artists_field_(self, mock_song_detail, mock_album_detail):
        """song.album.artists 需要请求网络"""
        song = provider.Song.get(11)
        album = song.album
        album.artists
        mock_album_detail.assert_called_once_with(album.identifier)

    @patch.object(API, 'artist_songs', return_value={'songs': data_artist_songs})
    @patch.object(API, 'artist_detail', return_value=data_artist)
    def test_artist_model(self, mock_artist_detail, mock_artist_songs):
        artist = provider.Artist.get(11)
        self.assertEqual(artist.name, '李宗盛')
        songs = artist.songs
        songs = artist.songs
        # 测试是否会多次调用接口
        mock_artist_songs.assert_called_once_with(artist.identifier)
        self.assertEqual(songs[0].identifier, 1772001102)

    @patch.object(API, 'playlist_detail', return_value=data_playlist)
    def test_playlists_model(self, mock_playlist_detail):
        playlist = provider.Playlist.get(11)
        self.assertEqual(playlist.name, '触碰心灵的经典之作')
        self.assertTrue(playlist.songs)
        self.assertTrue(playlist.uid)

    @patch.object(API, 'user_playlists', return_value=data_user_playlists)
    @patch.object(API, 'user_detail', return_value=data_user)
    def test_user_playlists_field(self, mock_user_detail, mock_user_playlists):
        user = provider.User.get(11)
        self.assertEqual(len(user.playlists), 2)
        mock_user_playlists.assert_called_once_with(user.identifier)

    @patch.object(API, 'search', return_value=data_search)
    def test_search(self, mock_search):
        s_result = provider.search('xx')
        songs = s_result.songs
        song = songs[0]
        self.assertEqual(song.identifier, 1769400313)
        self.assertEqual(song.source, 'xiami')
