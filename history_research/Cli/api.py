# -*- coding: utf-8 -*-


from controller_api import ControllerApi, ViewOp
from base.logger import LOG


"""apis for cli client

every api must have its return value
return {
    'code': int,
    'message': None or str,
    'result': None or ...
    }
"""


def run_func(func):
    data = dict()
    data['code'] = 404
    try:
        result = eval(func)
        LOG.info("执行函数成功 %s " % func)
        data['code'] = 200
        data['result'] = result
    except NameError:
        LOG.error("cli: %s command not found" % func)
        data['message'] = "command not found"
    except TypeError:
        LOG.error("cli: %s unknown arguement" % func)
        data['message'] = "arguments error"
    except Exception as e:
        LOG.error(str(e))
        data['message'] = "unknown error"
    return data


def play(mid=None):
    if mid is not None:
        return ControllerApi.play_specific_song_by_mid(mid)
    else:
        return ControllerApi.player.play()


def play_next():
    return ControllerApi.player.play_next()


def play_previous():
    return ControllerApi.player.play_last()


def pause():
    return ControllerApi.player.pause()


def search(text=None):
    if text is None:
        return False
    else:
        songs = ControllerApi.api.search(text)
        if not ControllerApi.api.is_response_ok(songs):
            return False
        return songs
