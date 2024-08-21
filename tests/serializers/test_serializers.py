from feeluown.app import App
from feeluown.player import Player, Playlist
from feeluown.serializers import serialize
from feeluown.library import SongModel, SimpleSearchResult
from feeluown.player import Metadata


def test_serialize_app(mocker):
    app = mocker.Mock(spec=App)
    app.task_mgr = mocker.Mock()
    app.live_lyric = mocker.Mock()
    app.live_lyric.current_sentence = ''
    player = Player()
    app.player = player
    app.playlist = Playlist(app)
    for format in ('plain', 'json'):
        serialize(format, app, brief=False)
        serialize(format, app, fetch=True)
    player.shutdown()


def test_serialize_metadata():
    metadata = Metadata({'title': 'hello world'})
    js = serialize('python', metadata)
    assert js['__type__'].endswith('player.Metadata')


def test_serialize_model():
    song = SongModel(identifier='1', title='hello', artists=[], duration=0)
    song_js = serialize('python', song)
    assert song_js['identifier'] == '1'
    assert song_js['title'] == 'hello'
    serialize('plain', song)  # should not raise error

    song_js = serialize('python', song, brief=True)
    assert song_js['identifier'] == '1'

    song_js = serialize('python', song, fetch=True)
    assert song_js['identifier'] == '1'


def test_serialize_search_result():
    song = SongModel(identifier='1', title='', artists=[], duration=0)
    result = SimpleSearchResult(q='', songs=[song])
    d = serialize('python', result)
    assert d['songs'][0]['identifier'] == '1'
    serialize('plain', result)  # should not raise error
