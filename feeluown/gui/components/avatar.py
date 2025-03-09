from typing import TYPE_CHECKING

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QPainter, QIcon, QPalette, QContextMenuEvent

from feeluown.library import UserModel, SupportsCurrentUser, Provider, \
    SupportsCurrentUserChanged
from feeluown.library import reverse
from feeluown.utils.aio import run_afn, run_fn
from feeluown.gui.provider_ui import UISupportsLoginOrGoHome, ProviderUiItem, \
    UISupportsLoginEvent
from feeluown.gui.widgets import SelfPaintAbstractIconTextButton
from feeluown.gui.drawers import SizedPixmapDrawer, AvatarIconDrawer
from feeluown.gui.helpers import painter_save

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Avatar(SelfPaintAbstractIconTextButton):
    """
    When no provider is selected, click this button will popup a menu,
    and let user select a provider. When a provider is selected, click this
    button will trigger `UISupportsLoginOrGoHome`. If the provider has
    a current user, this tries to show the user avatar.
    """

    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__('未登录', *args, **kwargs)

        self._app = app
        self._logging_state = {}
        self._avatar_drawer = None
        # In order to make the avatar/icon align to the left edge,
        # translate the painter to -self._padding and set different padding
        # for avatar-icon and avatar-image.
        self._avatar_padding = self._padding // 2
        # Leave 1px to draw line itself.
        # Theoretically, the line itself costs 1.5px and only 0.75px is needed.
        self._translate_x = 1 - self._padding
        self._avatar_translate_x = -self._avatar_padding
        self._icon_drawer = AvatarIconDrawer(self.height(), self._padding)
        self.clicked.connect(self.on_clicked)
        self.setToolTip('点击切换平台')

        self._app.library.provider_added.connect(self.on_provider_added)

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

    def on_provider_added(self, provider: Provider):
        if isinstance(provider, SupportsCurrentUserChanged):
            provider.current_user_changed.connect(
                self.create_provider_current_user_changed_cb(provider), weak=False)

    def create_provider_current_user_changed_cb(self, provider: Provider):
        def cb(user: UserModel):
            if user is not None:
                self._logging_state[provider.identifier] = user.name
            else:
                self._logging_state.pop(provider.identifier, None)
            if not self._app.current_pvd_ui_mgr.get():
                if self._logging_state:
                    self._text = '部分已登录'
                else:
                    self._text = '未登录'
                self.setToolTip(self._text)  # refresh tooltip
        return cb

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
        current_pvd_ui = self._app.current_pvd_ui_mgr.get()
        if current_pvd_ui == provider_ui and event == 2:
            return
        if event in (1, 2):
            run_afn(self.show_pvd_ui_current_user)
            run_afn(
                self._app.ui.sidebar.show_provider_current_user_playlists,
                provider_ui.provider
            )

    def on_pvd_ui_selected(self, pvd_ui):
        if isinstance(pvd_ui, UISupportsLoginEvent):
            pvd_ui.login_event.connect(self.on_provider_ui_login_event)
        if isinstance(pvd_ui, UISupportsLoginOrGoHome):
            pvd_ui.login_or_go_home()
        # Set current provider ui at the very last.
        # Must not set it before handling login event.
        self._app.current_pvd_ui_mgr.set(pvd_ui)

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

    async def _show_provider_current_user(self, source):
        self.setToolTip('')
        self._avatar_drawer = None
        provider = self._app.library.get(source)
        assert provider is not None
        user = None
        if isinstance(provider, SupportsCurrentUser):
            user = await run_fn(provider.get_current_user_or_none)

        if user is None:
            self._text = '未登录'
            return None
        if isinstance(user, UserModel) and user.avatar_url:
            self._text = user.name
            img_data = await run_afn(self._app.img_mgr.get, user.avatar_url,
                                     reverse(user))
            if img_data:
                p = self._avatar_padding
                w = self.height() - 2 * p
                rect = QRect(p, p, w, w)
                self._avatar_drawer = SizedPixmapDrawer.from_img_data(
                    img_data, rect, radius=0.5)
        return user

    def paint_border_bg_when_hover(self, *_, **__):
        pass

    def setToolTip(self, text):
        notes = f"后台已登录：{','.join(self._logging_state.keys()) or '无'}"
        super().setToolTip(text + '\n\n' + notes)

    def draw_text(self, painter):
        with painter_save(painter):
            if not self._avatar_drawer:
                painter.translate(self._translate_x, 0)
            super().draw_text(painter)

    def draw_icon(self, painter: QPainter):
        if self._avatar_drawer:
            with painter_save(painter):
                painter.translate(self._avatar_translate_x, 0)
                self._avatar_drawer.draw(painter)
        else:
            with painter_save(painter):
                painter.translate(self._translate_x, 0)
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
        layout.addWidget(Avatar(mockapp, height=length))
