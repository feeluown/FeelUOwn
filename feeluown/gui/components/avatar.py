from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QPainter, QIcon, QPalette, QContextMenuEvent

from feeluown.library import UserModel, NoUserLoggedIn
from feeluown.models.uri import reverse
from feeluown.utils.aio import run_afn, run_fn
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.uimodels.provider import ProviderUiItem
from feeluown.gui.drawers import PixmapDrawer, AvatarIconDrawer

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Avatar(SelfPaintAbstractSquareButton):

    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._provider_ui_item: Optional[ProviderUiItem] = None
        self._current_user: Optional[UserModel] = None
        self._pixmap = None
        self._avatar_drawer = None
        self._icon_drawer = AvatarIconDrawer(self.width(), self._padding)
        self.clicked.connect(self.on_clicked)
        self.setToolTip('点击登陆资源提供方')

    def on_clicked(self):
        if self._provider_ui_item is not None:
            self.maybe_goto_current_provider()
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
        self.maybe_goto_current_provider()
        run_afn(self.maybe_fetch_current_user)

    def maybe_goto_current_provider(self):
        provider = self._provider_ui_item
        provider.clicked.emit()
        # HACK: If the provider does not update the current page,
        # render the provider home page manually.
        # old_page = self._app.browser.current_page
        # new_page = self._app.browser.current_page
        # if new_page == old_page:
        #     self._app.browser.goto(page=f'/providers/{provider.name}')

    async def maybe_fetch_current_user(self):
        self._avatar_drawer = None
        try:
            self._current_user = await run_fn(self._app.library.provider_get_current_user,
                                              self._provider_ui_item.name)
        except NoUserLoggedIn:
            self._current_user = None

        if self._current_user is not None:
            self.setToolTip(f'{self._current_user.name} ({self._provider_ui_item.text})')
            if self._current_user.avatar_url:
                img_data = await run_afn(self._app.img_mgr.get,
                                         self._current_user.avatar_url,
                                         reverse(self._current_user))
                if img_data:
                    self._avatar_drawer = PixmapDrawer.from_img_data(img_data, self, radius=0.5)

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
