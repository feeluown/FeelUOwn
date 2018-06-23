import asyncio
import logging

from PyQt5.QtCore import QObject

from fuocore.netease.provider import NeteaseProvider
from feeluown.components.library import LibraryModel

from .model import NUserModel
from .ui import LoginDialog


logger = logging.getLogger(__name__)
provider = NeteaseProvider()


class Nem(QObject):

    def __init__(self, app):
        super(Nem, self).__init__(parent=app)
        self._app = app
        self.login_dialog = LoginDialog(
            verify_captcha=NUserModel.check_captcha,
            verify_userpw=NUserModel.check,
            create_user=NUserModel.create,
        )
        self.user = None
        self._library = LibraryModel(
            identifier='netease',
            name='网易云音乐',
            load_cb=self.ready_to_login,
        )

    def initialize(self):
        self._app.provider_manager.register(provider)
        left_panel = self._app.ui.left_panel
        self._app.libraries.add_library(self._library)

    def ready_to_login(self):
        if self.user is not None:
            logger.debug('You have already logined in.')
            return
        logger.debug('Trying to load last login user...')
        model = NUserModel.load()
        if model is None:
            logger.debug('Trying to load last login user...failed')
            self.login_dialog.show()
            self.login_dialog.load_user_pw()
            self.login_dialog.login_success.connect(self.login_as)
        else:
            logger.debug('Trying to load last login user...done')
            self.login_as(model)

    async def load_playlists(self):
        self._app.message('正在加载网易云音乐歌单')
        left_panel = self._app.ui.left_panel
        user = provider.get_user(self.user.uid)
        loop = asyncio.get_event_loop()
        playlists = await loop.run_in_executor(None, lambda: user.playlists)
        left_panel.set_playlists(playlists)

    def login_as(self, user):
        NUserModel.set_current_user(user)
        self.user = user
        self.user.save()
        loop = asyncio.get_event_loop()
        loop.create_task(self.load_playlists())
        self._library.name = '网易云音乐 - {}'.format(self.user.name)
