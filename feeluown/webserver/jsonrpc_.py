from typing import List, Any

from jsonrpc import JSONRPCResponseManager, dispatcher

from feeluown.fuoexec.fuoexec import fuoexec_get_globals


def initialize():
    dispatcher.add_method(lambda: "pong", name="ping")


def handle(data):
    print('handle data', data)
    response = JSONRPCResponseManager.handle(data, dispatcher)
    print('handle resp', response)
    return response.data
