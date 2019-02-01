import logging

from fuocore.provider import AbstractProvider
from fuocore.netease.api import API


logger = logging.getLogger(__name__)


class NeteaseProvider(AbstractProvider):
    def __init__(self):
        super().__init__()
        self.api = API()

    @property
    def identifier(self):
        return 'netease'

    @property
    def name(self):
        return '网易云音乐'

    def auth(self, user):
        assert user.cookies is not None
        self._user = user
        self.api.load_cookies(user.cookies)


provider = NeteaseProvider()


from .models import search  # noqa
provider.search = search
