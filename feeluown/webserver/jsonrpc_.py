from functools import wraps

from jsonrpc import JSONRPCResponseManager, Dispatcher

from feeluown.fuoexec.fuoexec import fuoexec_get_globals
from feeluown.serializers import serialize, deserialize


class DynamicDispatcher(Dispatcher):
    def __getitem__(self, key):
        try:
            return self.method_map[key]
        except KeyError:
            method = eval(key, fuoexec_get_globals())
            return method_wrapper(method)


def method_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        new_args = ()
        if args:
            new_args = [deserialize('python', arg) for arg in args]
        new_kwargs = {}
        if kwargs:
            new_kwargs = {}
            for k, v in kwargs.items():
                new_kwargs[k] = deserialize('python', v)
        return func(*new_args, **new_kwargs)
    return wrapper


dispatcher = DynamicDispatcher()


def initialize():
    dispatcher.add_method(lambda: "pong", name="ping")


def handle(data):
    response = JSONRPCResponseManager.handle(data, dispatcher)
    if 'result' in response.data:
        result = serialize('python', response.result)
        response.result = result
    return response.data
