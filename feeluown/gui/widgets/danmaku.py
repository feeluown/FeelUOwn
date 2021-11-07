import time

from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget

from feeluown.player import State


class DanmakuOverlay(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.setAutoFillBackground(False)

        self._timer = QTimer(self)  #: timer for hidding overlay
        self._timeout = 15  # 60fps

        self._running_danmaku = [
            (5, 10, '感觉好卡呀，为啥呢，heyheyhey？'),
            (10, 20, '周杰伦不香么？'),
            (17, 10, '帧数不够'),
            (23, 10, '尴尬!'),
        ]

        self._timer.timeout.connect(self.__on_timeout)
        self._app.player.state_changed.connect(self._on_player_state_changed, aioqueue=True)

    def _on_player_state_changed(self, state):
        if self._app.player.state == State.playing:
            print('start timer')
            self._timer.start(self._timeout)
        else:
            print('stop timer')
            self._timer.stop()

    def __on_timeout(self):
        self.parent().repaint()

    def paint(self, painter):
        # print(self._app.player.position)
        print(time.time(), self._app.player.position)
        #painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        #painter.fillRect(self.rect(), QColor('transparent'))
        if self._app.player.current_media:
            from feeluown.gui.helpers import resize_font
            w = self.width()
            position = self._app.player.position
            painter.save()
            font = painter.font()
            pen = painter.pen()
            pen.setColor(QColor('red'))
            painter.setPen(pen)
            resize_font(font, 5)
            painter.setFont(font)
            fm = painter.fontMetrics()

            for danmaku in self._running_danmaku:
                start, end, text = danmaku
                duration = 15
                width = fm.horizontalAdvance(text)
                if start < position < start+duration:
                    x = w - ((position - start) / duration * w)
                    painter.drawText(QRectF(x, 0, width, 60), Qt.AlignLeft, text)
            painter.restore()
        #painter.end()

    #def paintEvent(self, e):
    #    self.paint(painter)
