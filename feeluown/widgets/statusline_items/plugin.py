from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QLabel


class PluginStatus(QLabel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._total_count = 0
        self._enabled_count = 0

        self.setAlignment(Qt.AlignCenter)
        # FIXME: 暂时通过设置 5 个空格，来让整个文字显示居中
        self.setText('☯' + ' ' * 5)
        self.setMinimumWidth(40)

        self._app.plugin_mgr.scan_finished.connect(self.on_scan_finishd)

    def on_scan_finishd(self, plugins):
        self._total_count = len(plugins)
        for plugin in plugins:
            if plugin.is_enabled:
                self._enabled_count += 1
        plugins_alias = '\n'.join([p.alias for p in plugins])
        self.setToolTip('已经加载的插件：\n{}'.format(plugins_alias))

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        font = painter.font()
        pen = painter.pen()
        font.setPointSize(8)
        pen.setColor(QColor('grey'))
        painter.setFont(font)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        x = self.width() - 20
        y = self.height() - 5
        bottomright = QPoint(x, y)
        text = '{}/{}'.format(self._enabled_count, self._total_count)
        painter.drawText(bottomright, text)
