import logging
from contextlib import contextmanager

from fuocore.provider import AbstractProvider
from .api import API


logger = logging.getLogger(__name__)


class QQMusicProvider(AbstractProvider):
    def __init__(self):
        self.api = API()

        self._user = None

    @property
    def identifier(self):
        return 'qqmusic'

    @property
    def name(self):
        return 'QQ 音乐'

    @contextmanager
    def auth_as(self, user):
        old_user = self._user
        self.auth(user)
        try:
            yield
        finally:
            self.auth(old_user)

    def auth(self, user):
        assert user.cookies is not None
        self._user = user
        self.api.load_cookies(user.cookies)


provider = QQMusicProvider()


from .models import search
provider.search = search
