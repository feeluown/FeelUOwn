from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QPainter, QIcon, QPalette, QContextMenuEvent

from feeluown.library import NoUserLoggedIn, UserModel
from feeluown.library import reverse
from feeluown.utils.aio import run_afn, run_fn
from feeluown.gui.provider_ui import UISupportsLoginOrGoHome, ProviderUiItem, \
    UISupportsLoginEvent
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.drawers import PixmapDrawer, AvatarIconDrawer

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Avatar(SelfPaintAbstractSquareButton):
    """
    When no provider is selected, click this button will popup a menu,
    and let user select a provider. When a provider is selected, click this
    button will trigger `UISupportsLoginOrGoHome`. If the provider has
    a current user, this tries to show the user avatar.
    """

    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._avatar_drawer = None
        self._icon_drawer = AvatarIconDrawer(self.width(), self._padding)
        self.clicked.connect(self.on_clicked)
        self.setToolTip('点击登陆资源提供方')

    def on_clicked(self):
        pvd_ui = self._app.current_pvd_ui_mgr.get()
        if pvd_ui is not None:
            if isinstance(pvd_ui, UISupportsLoginOrGoHome):
                pvd_ui.login_or_go_home()
            return

        item = self._app.current_pvd_ui_mgr.get_item()
        if item is not None:
            item.clicked.emit()
        else:
            pos = self.cursor().pos()
            e = QContextMenuEvent(QContextMenuEvent.Mouse, pos, pos)
            self.contextMenuEvent(e)

    def contextMenuEvent(self, e) -> None:
        # pylint: disable=unnecessary-direct-lambda-call
        menu = QMenu()
        action = menu.addSection('切换账号')
        action.setDisabled(True)
        for item in self._app.pvd_uimgr.list_items():
            action = QAction(QIcon(item.colorful_svg or 'icons:feeluown.png'),
                             item.text,
                             parent=menu)
            action.setToolTip(item.desc)
            action.triggered.connect(
                (lambda item: lambda _: self.on_provider_selected(item))(item))
            menu.addAction(action)

        for pvd_ui in self._app.pvd_ui_mgr.list_all():
            action = QAction(QIcon(pvd_ui.get_colorful_svg() or 'icons:feeluown.png'),
                             pvd_ui.provider.meta.name,
                             parent=menu)
            action.triggered.connect(
                (lambda pvd_ui: lambda _: self.on_pvd_ui_selected(pvd_ui))(pvd_ui))
            menu.addAction(action)

        menu.exec_(e.globalPos())

    def on_provider_ui_login_event(self, provider_ui, event):
        if event in (1, 2):
            run_afn(self.show_pvd_ui_current_user)
            run_afn(
                self._app.ui.sidebar.show_provider_current_user_playlists,
                provider_ui.provider
            )

    def on_pvd_ui_selected(self, pvd_ui):
        self._app.current_pvd_ui_mgr.set(pvd_ui)
        if isinstance(pvd_ui, UISupportsLoginEvent):
            pvd_ui.login_event.connect(self.on_provider_ui_login_event)
        if isinstance(pvd_ui, UISupportsLoginOrGoHome):
            pvd_ui.login_or_go_home()
        run_afn(self.show_pvd_ui_current_user)

    def on_provider_selected(self, provider: ProviderUiItem):
        self._app.current_pvd_ui_mgr.set_item(provider)
        self.setToolTip(provider.text + '\n\n' + provider.desc)
        provider.clicked.emit()
        run_afn(self.show_provider_current_user)

    async def show_pvd_ui_current_user(self):
        pvd_ui = self._app.current_pvd_ui_mgr.get()
        name = pvd_ui.provider.meta.identifier
        user = await self._show_provider_current_user(name)
        if user is not None:
            self.setToolTip(f'{user.name} ({pvd_ui.provider.meta.name})')

    async def show_provider_current_user(self):
        item = self._app.current_pvd_ui_mgr.get_item()
        user = await self._show_provider_current_user(item.name)
        if user is not None:
            self.setToolTip(f'{user.name} ({item.text})')

    async def _show_provider_current_user(self, name):
        self.setToolTip('')
        self._avatar_drawer = None
        try:
            user = await run_fn(self._app.library.provider_get_current_user, name)
        except NoUserLoggedIn:
            user = None

        if user is None:
            return None
        if isinstance(user, UserModel) and user.avatar_url:
            img_data = await run_afn(self._app.img_mgr.get, user.avatar_url,
                                     reverse(user))
            if img_data:
                self._avatar_drawer = PixmapDrawer.from_img_data(img_data,
                                                                 self,
                                                                 radius=0.5)
        return user

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)

        if self._avatar_drawer:
            self._avatar_drawer.draw(painter)
        else:
            # If a provider is selected, draw a highlight circle.
            if self._app.current_pvd_ui_mgr.get_either() is not None:
                self._icon_drawer.fg_color = self.palette().color(QPalette.Highlight)
            self._icon_drawer.draw(painter)


if __name__ == '__main__':
    from unittest.mock import MagicMock
    from feeluown.gui.debug import simple_layout, mock_app

    length = 400

    with simple_layout() as layout, mock_app() as mockapp:
        mockapp.pvd_uimgr.list_items = MagicMock(return_value=[
            ProviderUiItem(
                '',
                'Hello World',
                '',
                'Hello World',
            ),
            ProviderUiItem(
                '',
                'Hello PyQt5',
                '',
                'Hello PyQt5',
            )
        ])
        layout.addWidget(Avatar(mockapp, length=length))
