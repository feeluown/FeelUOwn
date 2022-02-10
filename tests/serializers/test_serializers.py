from feeluown.app import App
from feeluown.player import Player, Playlist
from feeluown.serializers import serialize
from feeluown.library import SongModel
from feeluown.models import SongModel as SongModelV1


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


def test_serialize_model():
    song = SongModel(identifier='1', title='', artists=[], duration=0)
    song_js = serialize('python', song)
    assert song_js['identifier'] == '1'

    song_js = serialize('python', song, brief=True)
    assert song_js['identifier'] == '1'

    song_js = serialize('python', song, fetch=True)
    assert song_js['identifier'] == '1'


def test_serialize_model_v1():
    song = SongModelV1(identifier='1', title='', artists=[], duration=0)
    song_js = serialize('python', song)
    assert song_js['identifier'] == '1'
