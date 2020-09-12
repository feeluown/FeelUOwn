from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QTextOption

from feeluown.widgets.statusline import StatuslineLabel


class PluginStatus(StatuslineLabel):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self._app = app

        self._total_count = 0
        self._enabled_count = 0
        self._status_color = 'blue'
        self._app.plugin_mgr.scan_finished.connect(self.on_scan_finished)

    def on_scan_finished(self, plugins):
        self._total_count = len(plugins)
        for plugin in plugins:
            if plugin.is_enabled:
                self._enabled_count += 1
        plugins_alias = '\n'.join([p.alias for p in plugins])
        self.setToolTip('已经加载的插件：\n{}'.format(plugins_alias))
        self.setText(f'{self._enabled_count}')

    def drawInner(self, painter):
        inner_rect = QRectF(0, 0, self._inner_width, self._inner_height)
        painter.drawText(inner_rect, '☯', QTextOption(Qt.AlignCenter))
