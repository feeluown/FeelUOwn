from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, \
    QHBoxLayout, QOpenGLWidget, QLabel

from feeluown.player import State
from feeluown.gui.widgets import PlayPauseButton
from feeluown.gui.widgets.progress_slider import ProgressSlider
from feeluown.gui.widgets.size_grip import SizeGrip
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.labels import ProgressLabel, DurationLabel


class Button(TextButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)
        self.setFixedHeight(16)

    def sizeHint(self):
        fm = self.fontMetrics()
        rect = fm.boundingRect(self.text())
        return QSize(rect.width() + 6, rect.height())


class VideoPlayerCtlBar(QWidget):

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self._app = app

        # Create widgets.
        self._toggle_btn = PlayPauseButton(draw_circle=False)
        self._progress_slider = ProgressSlider(app)
        self._progress_label = ProgressLabel(app, self)
        self._duration_label = DurationLabel(app, self)
        self._size_grip = SizeGrip(parent=self)
        self._adhoc_btn_layout = QHBoxLayout()
        self._layout = QVBoxLayout(self)
        self._bottom_layout = QHBoxLayout()

        # Do initialization for widgets.
        self._toggle_btn.setCheckable(True)
        self._setup_ui()

        self._app.player.state_changed.connect(
            lambda x: self._toggle_btn.setChecked(x == State.playing),
            weak=False,
            aioqueue=True)
        self._toggle_btn.clicked.connect(self._app.player.toggle)

    def add_adhoc_btn(self, text: str) -> QPushButton:
        """
        .. versionadded: 4.0.1
        """
        btn = Button(text)
        self._adhoc_btn_layout.addWidget(btn)
        btn.setPalette(self.palette())
        return btn

    def clear_adhoc_btns(self):
        """
        .. versionadded: 4.0.1
        """
        while self._adhoc_btn_layout.count():
            item = self._adhoc_btn_layout.itemAt(0)
            self._adhoc_btn_layout.removeItem(item)
            if item.widget():
                item.widget().deleteLater()

    def _setup_ui(self):
        self.setAutoFillBackground(True)

        # Setup layout.
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._progress_slider)
        self._layout.addLayout(self._bottom_layout)

        # Setup bottom layout.
        self._layout.addStretch(0)
        self._bottom_layout.setSpacing(2)
        self._adhoc_btn_layout.setSpacing(4)
        self._bottom_layout.addWidget(self._toggle_btn)
        self._bottom_layout.addSpacing(6)
        self._bottom_layout.addWidget(self._progress_label)
        self._bottom_layout.addWidget(QLabel('/', self))
        self._bottom_layout.addWidget(self._duration_label)
        self._bottom_layout.addStretch(1)
        self._bottom_layout.addLayout(self._adhoc_btn_layout)
        self._bottom_layout.addSpacing(6)
        self._bottom_layout.addWidget(self._size_grip)

        # Setup widgets size.
        self._size_grip.setFixedSize(20, 20)

        # Customize the palette.
        palette = self.palette()
        palette.setColor(QPalette.Text, QColor('white'))
        palette.setColor(QPalette.ButtonText, QColor('white'))
        palette.setColor(QPalette.WindowText, QColor('white'))
        bg_color = QColor('black')
        bg_color.setAlpha(180)  # Make it semi-transparent.
        palette.setColor(QPalette.Window, bg_color)
        self.setPalette(palette)
        # It seems children don't inherit the palette, so we set palette for
        # children explicitly.
        for child in self.findChildren(QWidget):
            child.setPalette(palette)


class VideoOpenGLWidget(QOpenGLWidget):
    """Base class for widget which provides OpenGL based video rendering

    This widget has a overlay which currently contains a player control bar.
    """
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        # Define public attributes.
        self.overlay_auto_visible = True

        # Define protected attributes.
        self._gl_painters = set({})
        self._overlay_visible_timer = QTimer(self)
        self._overlay_visible_duration = 2000  # 2s

        # Define ui related objects and attributes.
        self.ctl_bar = VideoPlayerCtlBar(app=app, parent=self)
        self._layout = QVBoxLayout(self)

        # Do initialization.
        self.setMouseTracking(True)
        self._overlay_visible_timer.timeout.connect(self.hide_overlay)
        self._setup_ui()

    def _setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(1)
        self._layout.addWidget(self.ctl_bar)
        self.hide_overlay()

    def add_gl_painter(self, painter):
        """Add QPainter based gl painter.

        In paintGL, we invoke these painters one by one so that they can
        paint their own contents.

        :param painter: painter must impl `paint(opengl_widget)` method.

        .. versionadded: 3.7.13
        """
        # Simple validation
        assert hasattr(painter, 'paint'), \
            "painter must impl `paint` method."
        self._gl_painters.add(painter)

    def hide_overlay(self):
        """hide the overlay widget"""
        self.ctl_bar.hide()

    def show_overlay(self):
        """show the overlay widget"""
        self.ctl_bar.show()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        if self.overlay_auto_visible is True:
            self.show_overlay()
            self._overlay_visible_timer.start(self._overlay_visible_duration)

    def enterEvent(self, e):
        super().enterEvent(e)
        if self.overlay_auto_visible is True:
            self.show_overlay()
            self._overlay_visible_timer.start(self._overlay_visible_duration)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._overlay_visible_timer.start(self._overlay_visible_duration)


if __name__ == '__main__':
    from feeluown.gui.debug import simple_layout, mock_app

    with simple_layout(theme='dark') as layout, mock_app() as app:
        ctl_bar = VideoPlayerCtlBar(app)
        ctl_bar.add_adhoc_btn('全屏')
        ctl_bar.add_adhoc_btn('最小化')
        layout.addWidget(ctl_bar)
