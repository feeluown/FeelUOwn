from jsonrpc import JSONRPCResponseManager, dispatcher

from feeluown.fuoexec.fuoexec import fuoexec_get_globals
from feeluown.serializers import serialize


def initialize():
    dispatcher.add_method(lambda: "pong", name="ping")

    def method(name):
        method = eval(name, fuoexec_get_globals())
        return method, name

    for name in [
        # playlist
        'app.playlist.next',
        'app.playlist.previous',
        'app.playlist.list',
        # player
        'app.player.pause',
        'app.player.resume',
    ]:
        dispatcher.add_method(*method(name))


def handle(data):
    response = JSONRPCResponseManager.handle(data, dispatcher)
    if 'result' in response.data:
        result = serialize('python', response.result)
        response.result = result
    return response.data
