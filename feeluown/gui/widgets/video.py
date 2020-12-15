from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPalette, QPainter
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, \
    QHBoxLayout, QOpenGLWidget

from feeluown.player import State
from feeluown.widgets.progress_slider import ProgressSlider
from feeluown.widgets.size_grip import SizeGrip
from .labels import ProgressLabel, DurationLabel


class VideoOverlay(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._video_pp_btn = QPushButton()
        self._progress_slider = ProgressSlider(app)
        self._left_label = ProgressLabel(app, self)
        self._right_label = DurationLabel(app, self)

        # configure layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._top_layout = QHBoxLayout()
        self._bottom_layout = QHBoxLayout()
        self._layout.addStretch(0)
        self._layout.addLayout(self._top_layout)
        self._layout.addLayout(self._bottom_layout)
        # HELP: why must we add stretch around button to make sure
        # the button is properly rendered by Qt?
        self._top_layout.addStretch(0)
        self._top_layout.addWidget(self._video_pp_btn)
        self._top_layout.addStretch(0)
        self._bottom_layout.addSpacing(10)
        self._bottom_layout.addWidget(self._left_label)
        self._bottom_layout.addSpacing(5)
        self._bottom_layout.addWidget(self._progress_slider)
        self._bottom_layout.addSpacing(5)
        self._bottom_layout.addWidget(self._right_label)
        self._bottom_layout.addSpacing(10)

        self._video_pp_btn.setObjectName('video_pp_btn')
        self._video_pp_btn.setCheckable(True)

        # configure self
        # button size is set by stylesheet
        self.setFixedHeight(60)  # btn(36) + slider(20) + 5(remain)
        self._progress_slider.setFixedHeight(20)
        self._left_label.setFixedWidth(45)
        self._right_label.setFixedWidth(45)

        # signals
        self._app.player.state_changed.connect(
            lambda x: self._video_pp_btn.setChecked(x == State.playing),
            weak=False,
            aioqueue=True)
        self._video_pp_btn.clicked.connect(self._app.player.toggle)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color = self.palette().color(QPalette.Window)
        bg_color.setAlpha(180)
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(350, size.height())


class VideoOpenGLWidget(QOpenGLWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self._timer = QTimer(self)  #: timer for hidding overlay
        self._timeout = 2000  # unit: ms
        self._overlay_min_width = 360
        self._overlay_max_width = 480

        self._overlay = VideoOverlay(app=app, parent=self)
        self._size_grip = SizeGrip(parent=self)
        self._layout = QVBoxLayout(self)
        self._bottom_layout = QHBoxLayout()

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(20)
        self._layout.addWidget(self._overlay)
        self._layout.setAlignment(self._overlay, Qt.AlignHCenter)
        self._layout.addStretch(1)
        self._layout.addSpacing(10)
        self._layout.addLayout(self._bottom_layout)

        self._bottom_layout.addStretch(0)
        self._bottom_layout.addWidget(self._size_grip)
        self._size_grip.setFixedSize(20, 20)

        self._timer.timeout.connect(self.__on_timeout)
        self.setMouseTracking(True)
        self.hide_overlay()

    def hide_overlay(self):
        """hide the overlay widget"""
        self._overlay.hide()
        self._size_grip.hide()

    def show_overlay(self):
        """show the overlay widget"""
        self._overlay.show()
        self._size_grip.show()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        self.show_overlay()
        self._timer.start(self._timeout)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        max_width = min(self.width() - 50, self._overlay_max_width)
        self._overlay.setMaximumWidth(max_width)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.show_overlay()
        self._timer.start(self._timeout)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._timer.start(self._timeout)

    def __on_timeout(self):
        self.hide_overlay()
