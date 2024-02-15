import sys
from typing import Optional

from PyQt5.QtCore import QTimer, QEvent, Qt, QRect
from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QPushButton,
)
from PyQt5.QtGui import (
    QMouseEvent, QCursor, QPainter, QPalette, QBrush,
)

from feeluown.gui.helpers import darker_or_lighter
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.progress_slider import ProgressSlider
from feeluown.gui.components import (
    LineSongLabel, MediaButtonsV2, LyricButton, WatchButton, LikeButton,
    MVButton, VolumeSlider, SongSourceTag, PlayerProgressRatioLabel
)

IS_MACOS = sys.platform == 'darwin'


class MouseState:
    def __init__(self, e: QMouseEvent):
        self.start_pos = e.globalPos()
        self.current_pos = self.start_pos

    @property
    def moved(self) -> bool:
        return self.start_pos != self.current_pos


class Toolbar(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        button_width = 20
        self._song_btn_size = (16, 16)
        # self.setStyleSheet('border: 1px solid red;')

        self.song_source_tag = SongSourceTag(app=self._app, font_size=10)
        self.line_song_label = LineSongLabel(app=self._app)
        self.progress_slider = ProgressSlider(app=self._app)
        self.progress_label = PlayerProgressRatioLabel(app=self._app)
        self.volume_slider = VolumeSlider(app=self._app)
        self.media_buttons = MediaButtonsV2(app=self._app,
                                            spacing=0,
                                            button_width=button_width+5)
        self.lyric_button = LyricButton(app=self._app)
        self.like_button = LikeButton(app=self._app, size=self._song_btn_size)
        self.watch_button = WatchButton(app=self._app)
        self.mv_button = MVButton(app=self._app, height=self._song_btn_size[1])
        self.volume_button = QPushButton()

        self.volume_button.setObjectName('volume_btn')
        self.volume_button.setFixedWidth(button_width)
        self.volume_slider.setMaximumWidth(60)

        # Set margins/spacing explicitly because different platforms
        # has different default values.
        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(6)
        bottom_margin = 0 if IS_MACOS else 8
        self._layout.setContentsMargins(8, 8, 8, bottom_margin)

        self._v_layout = QVBoxLayout()
        self._song_layout = QHBoxLayout()
        self._btns_layout = QHBoxLayout()
        self._other_btns_layout = QVBoxLayout()

        self._layout.addLayout(self._v_layout)
        self._layout.addLayout(self._other_btns_layout)

        self._v_layout.setSpacing(0)
        self._v_layout.addLayout(self._song_layout)
        self._v_layout.addSpacing(3)
        self._v_layout.addStretch(0)
        self._v_layout.addWidget(self.progress_slider)
        self._v_layout.addStretch(0)
        self._v_layout.addLayout(self._btns_layout)

        if IS_MACOS:
            # On macOS, the default height of the slider is not enough to show
            # the slider handler, so set a minimum height for sliders.
            self.progress_slider.setMinimumHeight(24)
            self.volume_slider.setMinimumHeight(24)

        self._song_layout.setSpacing(self._song_btn_size[1]//2)
        self._song_layout.addWidget(self.song_source_tag)
        self._song_layout.addWidget(self.line_song_label)
        self._song_layout.addWidget(self.mv_button)
        self._song_layout.addWidget(self.like_button)

        self._other_btns_layout.addWidget(self.watch_button)
        self._other_btns_layout.addWidget(self.lyric_button)
        self.watch_button.hide()
        self.lyric_button.hide()

        self._btns_layout.setSpacing(0)
        self._btns_layout.addWidget(self.progress_label)
        self._btns_layout.addStretch(0)
        self._btns_layout.addWidget(self.media_buttons)
        self._btns_layout.addStretch(0)
        self._btns_layout.addWidget(self.volume_button)
        self._btns_layout.addWidget(self.volume_slider)


class AnimatedCoverLabel(CoverLabelV2):
    def __init__(self, app, padding=6, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._padding = padding
        self._angle: float = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self.on_timeout)
        self._timer.start(16)

    def on_timeout(self):
        self._angle += 0.2
        self.update()

    def paintEvent(self, e):
        radius = self._radius
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        center = (self.width()//2, self.height()//2)

        painter.save()
        painter.translate(*center)
        painter.rotate(self._angle)
        painter.translate(-center[0], -center[1])
        painter.setPen(Qt.NoPen)

        # Draw border.
        color = darker_or_lighter(self.palette().color(QPalette.Background), 115)
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(self.rect(), radius, radius)

        pixmap = self.drawer.get_pixmap()
        if pixmap is not None:
            size = pixmap.size()
            y = (size.height() - self.height()) // 2
            rect = QRect(self._padding, y+self._padding,
                         self.width()-self._padding*2, self.height()-self._padding*2)
            brush = QBrush(pixmap)
            painter.setBrush(brush)
            painter.drawRoundedRect(rect, radius, radius)

        painter.restore()
        painter.end()


class FloatingBox(QFrame):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._height = 100
        self._padding = 6

        self._app = app
        self.setMouseTracking(True)

        self._timer = QTimer(self)

        # Windows movement control.
        self._mouse_state: Optional[MouseState] = None

        self.toolbar = Toolbar(app=self._app)
        self.circle = AnimatedCoverLabel(app=self._app,
                                         radius=self._height // 2,
                                         padding=self._padding)
        self.toolbar.installEventFilter(self)
        self.circle.installEventFilter(self)
        self.circle.setMouseTracking(True)

        self.circle.setFixedSize(self._height, self._height)
        self.toolbar.setFixedSize(300, self._height)
        self.setFixedHeight(self._height)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.toolbar)
        self._layout.addWidget(self.circle)
        self.maybe_hide_toolbar()

        self._timer.timeout.connect(self.maybe_hide_toolbar)

    def paintEvent(self, e):
        super().paintEvent(e)

        if not self.toolbar.isVisible():
            return

        # Draw background for toolbar.
        new_bg_color = darker_or_lighter(self.palette().color(QPalette.Background), 115)
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.save()
        painter.setBrush(new_bg_color)
        painter.drawRoundedRect(
            QRect(0, 0, self.width()-self._height//2, self._height), 3, 3)
        # painter.drawEllipse(self.circle.rect())
        painter.restore()

    async def show_cover(self, *args, **kwargs):
        await self.circle.show_cover(*args, **kwargs)

    def maybe_show_toolbar(self):
        if not self.toolbar.isVisible():
            self.toolbar.show()
            self.setFixedWidth(self.circle.width() + self.toolbar.width())
            self.move(self.pos().x()-self.toolbar.width(), self.pos().y())

    def maybe_hide_toolbar(self):
        if self.toolbar.isVisible():
            pos = self.toolbar.mapFromGlobal(QCursor.pos())
            if self.rect().contains(pos):
                return
        self.toolbar.hide()
        self.move(self.pos().x()+self.toolbar.width(), self.pos().y())
        self._timer.stop()
        self.setFixedWidth(self.circle.width())

    def mousePressEvent(self, e):
        self._mouse_state = MouseState(e)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent):
        self.maybe_show_toolbar()
        self._timer.start(1000)

        # NOTE: e.button() == Qt.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._mouse_state is not None:
            delta = e.globalPos() - self._mouse_state.current_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._mouse_state.current_pos = e.globalPos()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        # If the window is moved, intercept the event.
        moved = self._mouse_state is not None and self._mouse_state.moved
        self._mouse_state = None
        if not moved:
            super().mouseReleaseEvent(e)

    def eventFilter(self, obj, event):
        if obj in self.children() and event.type() == QEvent.MouseMove:
            self.maybe_show_toolbar()
            self._timer.start(1000)
            return False
        return False


if __name__ == '__main__':
    import os

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QDir
    from PyQt5.QtGui import QImage
    from unittest.mock import MagicMock

    from feeluown.gui.theme import ThemeManager

    icons_dir = os.path.join('feeluown', 'gui/assets/icons')
    QDir.addSearchPath('icons', icons_dir)

    img = QImage()
    # !!! You should change the image filename.
    img_fn = '7c90bb4edfa99cae1d142a33ebe26673-1685249600'
    img_fp = os.path.expanduser(f'~/.FeelUOwn/cache/{img_fn}')
    with open(img_fp, 'rb') as f:
        img.loadFromData(f.read())

    app = MagicMock()
    qapp = QApplication([])
    theme_mgr = ThemeManager(app)
    box = FloatingBox(app)
    box.setWindowFlags(Qt.FramelessWindowHint)
    box.setAttribute(Qt.WA_TranslucentBackground)
    box.circle.show_img(img)
    box.toolbar.line_song_label.setText('哈哈哈 - 嘿嘿')
    box.show()
    box.move(600, 400)
    theme_mgr.load_light()
    qapp.exec()
