from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton
from feeluown.widgets.magicbox import MagicBox
from feeluown.widgets.statusline import StatusLine, StatusLineItem
from feeluown.widgets.statusline_items import PluginStatus


class BottomPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)

        self.back_btn = QPushButton('⇦', self)
        self.forward_btn = QPushButton('⇨', self)
        self.magicbox = MagicBox(self._app)
        self.status_line = StatusLine(self._app)
        self.back_btn.setObjectName('back_btn')
        self.forward_btn.setObjectName('forward_btn')
        self.setObjectName('bottom_panel')

        self.plugin_status_line_item = StatusLineItem(
            'plugin',
            PluginStatus(self._app))
        self.status_line.add_item(self.plugin_status_line_item)

        self._layout.addWidget(self.back_btn)
        self._layout.addWidget(self.forward_btn)
        self._layout.addWidget(self.magicbox)
        self._layout.addWidget(self.status_line)

        height = self.magicbox.height()
        self.setFixedHeight(height)
        self.back_btn.setFixedWidth(height)
        self.forward_btn.setFixedWidth(height)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.back_btn.clicked.connect(self._app.browser.back)
        self.forward_btn.clicked.connect(self._app.browser.forward)
