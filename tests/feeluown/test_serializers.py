from feeluown.player import Player, Playlist
from feeluown.serializers import serialize

from feeluown.app import App
from feeluown.serializers.app import *  # noqa


def test_serialize_app(mocker):
    app = mocker.Mock(spec=App)
    app.task_mgr = mocker.Mock()
    app.live_lyric = mocker.Mock()
    app.live_lyric.current_sentence = ''
    player = Player(Playlist(app))
    app.player = player
    app.playlist = player.playlist
    for format in ('plain', 'json'):
        serialize(format, app, brief=False)
        serialize(format, app, fetch=True)
    player.shutdown()
