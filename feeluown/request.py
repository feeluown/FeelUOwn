import requests


class Request(object):
    def __init__(self, app):
        self._app = app

    def get(*args, **kw):
        res = requests.get(*args, **kw)
        if res.status_code == 200:
            return res
        pass

    def post(*args, **kw):
        res = requests.post(*args, **kw)
        if res.status_code == 200:
            return res
        return None
