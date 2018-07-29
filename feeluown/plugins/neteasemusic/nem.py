import asyncio
import logging

from PyQt5.QtCore import QObject

from fuocore.netease.provider import provider
from fuocore.netease.models import NUserModel, search

from .login_controller import LoginController
from .ui import LoginDialog


logger = logging.getLogger(__name__)


class Nem(QObject):

    def __init__(self, app):
        super(Nem, self).__init__(parent=app)
        self._app = app
        self.login_dialog = LoginDialog(
            verify_captcha=LoginController.check_captcha,
            verify_userpw=LoginController.check,
            create_user=LoginController.create,
        )
        self._user = None
        self._pm = None

    def ready_to_login(self):
        if self._user is not None:
            logger.debug('You have already logined in.')
            return
        logger.debug('Trying to load last login user...')
        user = LoginController.load()
        if user is None or 'MUSIC_U' not in user.cookies:
            logger.debug('Trying to load last login user...failed')
            self.login_dialog.show()
            self.login_dialog.load_user_pw()
            self.login_dialog.login_success.connect(
                lambda user: asyncio.ensure_future(self.login_as(user)))
        else:
            logger.debug('Trying to load last login user...done')
            asyncio.ensure_future(self.login_as(user))

    async def login_as(self, user):
        provider.auth(user)
        self._user = user
        LoginController.save(user)
        left_panel = self._app.ui.left_panel
        loop = asyncio.get_event_loop()
        self._pm.name = '网易云音乐 - {}'.format(user.name)
        playlists = await loop.run_in_executor(None, lambda: user.playlists)
        self._app.playlists.add(playlists)
        self._app.playlists.add(user.fav_playlists, is_fav=True)
