import logging

from fuocore.provider import AbstractProvider
from fuocore.xiami.api import API


logger = logging.getLogger(__name__)


class XiamiProvider(AbstractProvider):
    def __init__(self):
        super().__init__()
        self.api = API()

    @property
    def identifier(self):
        return 'xiami'

    @property
    def name(self):
        return '虾米音乐'

    def auth(self, user):
        assert user.access_token is not None
        self._user = user
        self.api.set_access_token(user.access_token)


provider = XiamiProvider()


# 让 provider 能够发现对应 Model
from .models import search  # noqa

provider.search = search
