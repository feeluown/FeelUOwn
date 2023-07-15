from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QPainter, QIcon, QPalette, QContextMenuEvent

from feeluown.library import NoUserLoggedIn
from feeluown.models.uri import reverse
from feeluown.utils.aio import run_afn, run_fn
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.uimodels.provider import ProviderUiItem
from feeluown.gui.drawers import PixmapDrawer, AvatarIconDrawer

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Avatar(SelfPaintAbstractSquareButton):
    """
    When no provider is selected, click this button will popup a menu,
    and let user select a provider. When a provider is selected, click this
    button will trigger `provider_ui_item.clicked`. If the provider has
    a current user, this tries to show the user avatar.
    """

    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._provider_ui_item: Optional[ProviderUiItem] = None
        self._avatar_drawer = None
        self._icon_drawer = AvatarIconDrawer(self.width(), self._padding)
        self.clicked.connect(self.on_clicked)
        self.setToolTip('点击登陆资源提供方')

    def on_clicked(self):
        if self._provider_ui_item is not None:
            self._provider_ui_item.clicked.emit()
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
            action = QAction(
                QIcon(item.colorful_svg or 'icons:feeluown.png'),
                item.text,
                parent=menu
            )
            action.setToolTip(item.desc)
            action.triggered.connect(
                (lambda item: lambda _: self.on_provider_selected(item))(item))
            menu.addAction(action)
        menu.exec_(e.globalPos())

    def on_provider_selected(self, provider: ProviderUiItem):
        self._provider_ui_item = provider
        self.setToolTip(provider.text + '\n\n' + provider.desc)
        self._provider_ui_item.clicked.emit()
        run_afn(self.show_provider_current_user)

    async def show_provider_current_user(self):
        self._avatar_drawer = None
        try:
            user = await run_fn(
                self._app.library.provider_get_current_user,
                self._provider_ui_item.name)
        except NoUserLoggedIn:
            user = None

        if user is not None:
            self.setToolTip(f'{user.name} ({self._provider_ui_item.text})')
            if user.avatar_url:
                img_data = await run_afn(self._app.img_mgr.get,
                                         user.avatar_url,
                                         reverse(user))
                if img_data:
                    self._avatar_drawer = PixmapDrawer.from_img_data(
                        img_data, self, radius=0.5)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)

        if self._avatar_drawer:
            self._avatar_drawer.draw(painter)
        else:
            # If a provider is selected, draw a highlight circle.
            if self._provider_ui_item is not None:
                self._icon_drawer.fg_color = self.palette().color(QPalette.Highlight)
            self._icon_drawer.draw(painter)


if __name__ == '__main__':
    from unittest.mock import MagicMock
    from feeluown.gui.debug import simple_layout, mock_app

    length = 400

    with simple_layout() as layout, mock_app() as mockapp:
        mockapp.pvd_uimgr.list_items = MagicMock(return_value=[
            ProviderUiItem('', 'Hello World', '', 'Hello World', ),
            ProviderUiItem('', 'Hello PyQt5', '', 'Hello PyQt5', )
        ])
        layout.addWidget(Avatar(mockapp, length=length))
