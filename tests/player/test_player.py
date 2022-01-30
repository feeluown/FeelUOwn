import os
import time
from unittest import TestCase, skipIf, mock

import pytest

from tests.helpers import cannot_play_audio
from feeluown.media import Media
from feeluown.player import State, Playlist, PlaybackMode, Player as MpvPlayer  # noqa


MP3_URL = os.path.join(os.path.dirname(__file__),
                       '../../data/test.m4a')
MPV_SLEEP_SECOND = 0.1  # 留给 MPV 反应的时间


app_mock = mock.MagicMock()


class FakeSongModel:  # pylint: disable=all
    class meta:
        support_multi_quality = False

    url = ''


class Meta:
    support_multi_quality = True


class FakeValidSongModel:
    meta = Meta
    url = MP3_URL

    def select_media(self, _):
        return MP3_URL, _


@pytest.fixture
def mpvplayer():
    player = MpvPlayer(Playlist(app_mock))
    player.volume = 0
    yield player
    player.stop()
    # HELP: player.shutdown() causes error on Windows
    #  Windows fatal exception: code 0xe24c4a02
    # Ref: https://github.com/feeluown/FeelUOwn/runs/4996179558
    player.shutdown()


@skipIf(cannot_play_audio, '')
def test_seek(mpvplayer, mocker):
    mock_changed_emit = mocker.patch.object(mpvplayer.position_changed, 'emit')
    mock_seeked_emit = mocker.patch.object(mpvplayer.seeked, 'emit')
    mpvplayer.play(MP3_URL)
    time.sleep(MPV_SLEEP_SECOND)
    assert not mock_seeked_emit.called
    assert mock_changed_emit.called
    mpvplayer.position = 100
    mock_seeked_emit.assert_called_once_with(100)


class TestPlayer(TestCase):

    def setUp(self):
        self.player = MpvPlayer(Playlist(app_mock))
        self.player.volume = 0

    def tearDown(self):
        self.player.stop()
        self.player.shutdown()

    @skipIf(cannot_play_audio, '')
    def test_play(self):
        self.player.play(MP3_URL)
        self.player.stop()

    @skipIf(cannot_play_audio, '')
    def test_duration(self):
        # This may failed?
        self.player.play(MP3_URL)
        time.sleep(MPV_SLEEP_SECOND)
        self.assertIsNotNone(self.player.duration)

    @skipIf(cannot_play_audio, '')
    def test_play_pause_toggle_resume_stop(self):
        self.player.play(MP3_URL)
        time.sleep(MPV_SLEEP_SECOND)
        self.player.toggle()
        self.assertEqual(self.player.state, State.paused)
        self.player.resume()
        self.assertEqual(self.player.state, State.playing)
        self.player.pause()
        self.assertEqual(self.player.state, State.paused)
        self.player.stop()
        self.assertEqual(self.player.state, State.stopped)

    @skipIf(cannot_play_audio, '')
    def test_set_volume(self):
        cb = mock.Mock()
        self.player.volume_changed.connect(cb)
        self.player.volume = 30
        self.assertEqual(self.player.volume, 30)
        cb.assert_called_once_with(30)

    @mock.patch('feeluown.player.mpvplayer._mpv_set_option_string')
    def test_play_media_with_http_headers(self, mock_set_option_string):
        media = Media('http://xxx', http_headers={'referer': 'http://xxx'})
        self.player.play(media)
        assert mock_set_option_string.called
        self.player.stop()


class TestPlaylist(TestCase):
    def setUp(self):
        self.s1 = FakeSongModel()
        self.s2 = FakeSongModel()
        self.playlist = Playlist(app_mock)
        self.playlist.add(self.s1)
        self.playlist.add(self.s2)

    def tearDown(self):
        self.playlist.clear()

    def test_add(self):
        self.playlist.add(self.s1)
        self.assertEqual(len(self.playlist), 2)

    def test_getitem(self):
        self.assertEqual(self.playlist[1], self.s2)

    def test_mark_as_bad(self):
        self.assertEqual(self.playlist.next_song, self.s1)
        self.playlist.mark_as_bad(self.s1)
        self.assertEqual(self.playlist.next_song, self.s2)

    def test_list(self):
        self.assertIn(self.s1, self.playlist.list())


class TestPlayerAndPlaylist(TestCase):

    def setUp(self):
        self.playlist = Playlist(app_mock)
        self.player = MpvPlayer()
        self.player.set_playlist(self.player)

    def tearDown(self):
        self.player.stop()
        self.player.shutdown()

    @skipIf(cannot_play_audio, '')
    @mock.patch.object(MpvPlayer, 'play')
    def test_remove_current_song_2(self, mock_play):
        """当播放列表只有一首歌时，移除它"""
        s1 = FakeValidSongModel()
        self.playlist.current_song = s1
        time.sleep(MPV_SLEEP_SECOND)  # 让 Mpv 真正的开始播放
        self.playlist.remove(s1)
        self.assertEqual(len(self.playlist), 0)
        self.assertEqual(self.player.state, State.stopped)
