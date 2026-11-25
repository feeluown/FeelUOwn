import time

import pytest

from feeluown.library import reverse
from feeluown.player import RecentlyPlayed, Playlist
from feeluown.player.smart_playlist import (
    SmartPlaylistManager,
    SmartRule,
    SmartSort,
)


@pytest.fixture()
def playlist(app_mock):
    return Playlist(app_mock)


def _play(rp, song, ts=None):
    rp.record_play(song, timestamp=ts)


def test_play_counts_and_most_played(playlist, song1, song2, song3):
    rp = RecentlyPlayed(playlist)
    now = time.time()
    _play(rp, song1, now - 10)
    _play(rp, song1, now - 5)
    _play(rp, song2, now - 3)

    counts = rp.get_play_counts()
    uri1 = reverse(song1)
    uri2 = reverse(song2)
    assert counts[uri1] == 2
    assert counts[uri2] == 1

    top = rp.get_most_played(limit=2)
    assert top[0] == song1
    assert top[1] == song2

    # Time range filtering: only plays in last 6 seconds.
    recent_counts = rp.get_play_counts(time_range_days=6 / 86400, now=now)
    assert recent_counts.get(uri1) == 1
    assert recent_counts.get(uri2) == 1
    assert uri1 not in rp.get_play_counts(time_range_days=1 / 86400, now=now + 86400 * 2)


def test_recent_list_and_state_roundtrip(playlist, song1, song2, library):
    from feeluown.library import Resolver
    Resolver.library = library
    rp = RecentlyPlayed(playlist)
    _play(rp, song1, time.time() - 20)
    _play(rp, song2, time.time() - 10)
    assert rp.list_songs()[0] == song2

    state = rp.get_state()
    assert len(state) == 2

    rp2 = RecentlyPlayed(playlist)
    rp2.load_state(state)
    assert rp2.list_songs()[0] == song2
    uri1 = reverse(song1)
    assert rp2.get_play_counts()[uri1] == 1


def test_smart_evaluate_sort_and_filter(app_mock, playlist, song1, song2, song3):
    rp = RecentlyPlayed(playlist)
    app_mock.recently_played = rp
    app_mock.playlist = playlist
    mgr = SmartPlaylistManager(app_mock, filepath=None)

    now = time.time()
    _play(rp, song1, now - 30)
    _play(rp, song1, now - 20)
    _play(rp, song1, now - 10)
    _play(rp, song2, now - 5)
    # song3 never played: should not appear.

    rule = SmartRule(sort_by=SmartSort.play_count_desc.value, limit=10)
    songs = mgr.evaluate(rule)
    assert songs[0] == song1
    assert songs[1] == song2
    assert song3 not in songs

    rule_recent = SmartRule(sort_by=SmartSort.last_played_desc.value, limit=10)
    songs = mgr.evaluate(rule_recent)
    assert songs[0] == song2

    rule_limited = SmartRule(
        sort_by=SmartSort.play_count_desc.value, limit=1, min_play_count=2
    )
    songs = mgr.evaluate(rule_limited)
    assert songs == [song1]

    rule_sources = SmartRule(
        sort_by=SmartSort.play_count_desc.value, limit=10, sources=['no-such-source']
    )
    assert mgr.evaluate(rule_sources) == []


def test_smart_manager_load_seed_and_activate(tmp_path, app_mock, playlist, song1):
    rp = RecentlyPlayed(playlist)
    app_mock.recently_played = rp
    app_mock.playlist = playlist
    path = tmp_path / 'smart.json'
    mgr = SmartPlaylistManager(app_mock, filepath=str(path))
    mgr.load()
    assert len(mgr.list_all()) == 3
    assert path.exists()

    _play(rp, song1, time.time())
    songs = mgr.activate('most-played')
    assert song1 in songs
    assert playlist.list() == songs
    assert mgr.active_id == 'most-played'
    mgr.deactivate()
    assert mgr.active_id is None


def test_smart_rule_from_dict_defaults():
    rule = SmartRule.from_dict({'sort_by': 'unknown-sort'})
    assert rule.sort_by == SmartSort.play_count_desc.value
    assert rule.limit == 50
