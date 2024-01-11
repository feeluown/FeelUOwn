from jsonrpc import JSONRPCResponseManager, Dispatcher

from feeluown.fuoexec.fuoexec import fuoexec_get_globals
from feeluown.serializers import serialize


class DynamicDispatcher(Dispatcher):
    def __getitem__(self, key):
        try:
            return self.method_map[key]
        except KeyError:
            method = eval(key, fuoexec_get_globals())
            return method


dispatcher = DynamicDispatcher()


def initialize():
    dispatcher.add_method(lambda: "pong", name="ping")


def handle(data):
    response = JSONRPCResponseManager.handle(data, dispatcher)
    if 'result' in response.data:
        result = serialize('python', response.result)
        response.result = result
    return response.data
