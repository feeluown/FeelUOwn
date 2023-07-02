from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QPainter, QIcon, QPalette

from feeluown.library import UserModel
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.widgets.selfpaint_btn import paint_round_bg_when_hover
from feeluown.gui.uimodels.provider import ProviderUiItem

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class Avatar(SelfPaintAbstractSquareButton):

    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._provider_ui_item: Optional[ProviderUiItem] = None
        self._current_user: Optional[UserModel] = None

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
        provider.clicked.emit()
        self._provider_ui_item = provider
        self.setToolTip(provider.text + '\n\n' + provider.desc)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        has_avatar = False
        if self._current_user is not None and self._current_user.avatar_url:
            has_avatar = True
            # Draw avatar.

        if not has_avatar:
            pen = painter.pen()
            pen.setWidthF(1.5)
            painter.setPen(pen)

            # If a provider is selected, draw a highlight circle.
            if self._provider_ui_item is not None:
                painter.setPen(self.palette().color(QPalette.Highlight))

            diameter = self.width() // 3
            # Draw circle.
            painter.drawEllipse(diameter, self._padding, diameter, diameter)
            # Draw body.
            x, y = self._padding, self.height() // 2
            width, height = self.width() // 2, self.height() // 2
            painter.drawArc(x, y, width, height, 0, 60*16)
            painter.drawArc(x, y, width, height, 120*16, 60*16)


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