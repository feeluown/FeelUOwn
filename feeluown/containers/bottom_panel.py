from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout

from feeluown.widgets.magicbox import MagicBox
from feeluown.widgets.statusline import StatusLine, StatusLineItem
from feeluown.widgets.statusline_items import PluginStatus


class BottomPanel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.back_btn = QPushButton('⇦', self)
        self.forward_btn = QPushButton('⇨', self)
        self.magicbox = MagicBox(self._app)
        self.status_line = StatusLine(self._app)

        # initialize widgets
        self.status_line.add_item(StatusLineItem('plugin', PluginStatus(self._app)))
        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)

        self.back_btn.clicked.connect(self._app.browser.back)
        self.forward_btn.clicked.connect(self._app.browser.forward)

        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName('bottom_panel')
        self.back_btn.setObjectName('back_btn')
        self.forward_btn.setObjectName('forward_btn')

        self._layout.addWidget(self.back_btn)
        self._layout.addWidget(self.forward_btn)
        self._layout.addSpacing(80)
        self._layout.addWidget(self.magicbox)
        self._layout.addSpacing(80)
        self._layout.addWidget(self.status_line)

        # assume the magicbox height is about 30
        h_margin, v_margin = 5, 15
        height = self.magicbox.height()

        self.setFixedHeight(height + v_margin * 2)
        self._layout.setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        self._layout.setSpacing(0)
