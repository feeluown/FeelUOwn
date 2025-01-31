from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5.QtWidgets import (
    QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout,
    QApplication,
)
from PyQt5.QtGui import (
    QColor, QLinearGradient, QPalette, QPainter,
)

from feeluown.player import PlaybackMode, SongsRadio, AIRadio, AI_RADIO_SUPPORTED
from feeluown.gui.helpers import fetch_cover_wrapper, esc_hide_widget
from feeluown.gui.components.player_playlist import PlayerPlaylistView
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.tabbar import TabBar
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
    SongMiniCardListDelegate,
)
from feeluown.utils.reader import create_reader


PlaybackModeName = {
    PlaybackMode.one_loop: '单曲循环',
    PlaybackMode.sequential: '顺序播放',
    PlaybackMode.loop: '循环播放',
    PlaybackMode.random: '随机播放',
}
PlaybackModes = list(PlaybackModeName.keys())


def acolor(s, a):
    """Create color with it's name and alpha"""
    color = QColor(s)
    color.setAlpha(a)
    return color


class PlaylistOverlay(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._tabbar = TabBar(self)
        self._clear_playlist_btn = TextButton('清空播放队列')
        self._playback_mode_switch = PlaybackModeSwitch(app)
        self._goto_current_song_btn = TextButton('跳转到当前歌曲')
        self._songs_radio_btn = TextButton('自动续歌')
        self._ai_radio_btn = TextButton('AI电台')
        # Please update the list when you add new buttons.
        self._btns = [
            self._clear_playlist_btn,
            self._playback_mode_switch,
            self._goto_current_song_btn,
            self._songs_radio_btn,
        ]
        self._stacked_layout = QStackedLayout()
        self._shadow_width = 15
        self._view_options = dict(row_height=60, no_scroll_v=False)
        self._player_playlist_view = PlayerPlaylistView(self._app, **self._view_options)

        # AutoFillBackground should be disabled for PlaylistOverlay so that shadow
        # effects can be simulated. AutoFillBackground should be enabled for tabbar.
        self._tabbar.setAutoFillBackground(True)

        self._clear_playlist_btn.clicked.connect(self._app.playlist.clear)
        self._goto_current_song_btn.clicked.connect(self.goto_current_song)
        self._songs_radio_btn.clicked.connect(self.enter_songs_radio)
        self._ai_radio_btn.clicked.connect(self.enter_ai_radio)
        esc_hide_widget(self)
        q_app = QApplication.instance()
        assert q_app is not None  # make type checker happy.
        # type ignore: q_app has focusChanged signal, but type checker can't find it.
        q_app.focusChanged.connect(self.on_focus_changed)  # type: ignore
        self._app.installEventFilter(self)
        self._tabbar.currentChanged.connect(self.show_tab)

        if (
            AI_RADIO_SUPPORTED is True
            and self._app.config.OPENAI_API_KEY
            and self._app.config.OPENAI_MODEL
            and self._app.config.OPENAI_API_BASEURL
        ):
            self._ai_radio_btn.clicked.connect(self.enter_ai_radio)
        else:
            self._ai_radio_btn.setDisabled(True)
        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._btn_layout = QHBoxLayout()
        self._btn_layout2 = QHBoxLayout()
        self._layout.setContentsMargins(self._shadow_width, 0, 0, 0)
        self._layout.setSpacing(0)
        self._btn_layout.setContentsMargins(7, 7, 7, 7)
        self._btn_layout.setSpacing(7)
        self._btn_layout2.setContentsMargins(7, 0, 7, 7)
        self._btn_layout2.setSpacing(7)

        self._tabbar.setDocumentMode(True)
        self._tabbar.addTab('播放列表')
        self._tabbar.addTab('最近播放')
        self._layout.addWidget(self._tabbar)
        self._layout.addLayout(self._btn_layout)
        self._layout.addLayout(self._btn_layout2)
        self._layout.addLayout(self._stacked_layout)

        self._btn_layout.addWidget(self._clear_playlist_btn)
        self._btn_layout.addWidget(self._playback_mode_switch)
        self._btn_layout.addWidget(self._goto_current_song_btn)
        self._btn_layout2.addWidget(self._songs_radio_btn)
        self._btn_layout2.addWidget(self._ai_radio_btn)
        self._btn_layout.addStretch(0)
        self._btn_layout2.addStretch(0)

    def on_focus_changed(self, _, new):
        """
        Hide the widget when it loses focus.
        """
        if not self.isVisible():
            return
        # When the app is losing focus, the new is None.
        if new is None or new is self or new in self.findChildren(QWidget):
            return
        self.hide()

    def goto_current_song(self):
        view = self._stacked_layout.currentWidget()
        assert isinstance(view, PlayerPlaylistView)
        view.scroll_to_current_song()

    def enter_songs_radio(self):
        songs = self._app.playlist.list()
        if not songs:
            self._app.show_msg('播放队列为空，不能激活“自动续歌”功能')
        else:
            radio = SongsRadio(self._app, songs)
            self._app.fm.activate(radio.fetch_songs_func, reset=False)
            self._app.show_msg('“自动续歌”功能已激活')

    def enter_ai_radio(self):
        if self._app.playlist.list():
            radio = AIRadio(self._app)
            self._app.fm.activate(radio.fetch_songs_func, reset=False)
            self._app.show_msg('已经进入 AI 电台模式 ~')
        else:
            self._app.show_msg('播放列表为空，暂时不能开启 AI 电台')

    def show_tab(self, index):
        if not self.isVisible():
            return

        if index == 0:
            self._show_btns()
            view = self._player_playlist_view
        else:
            self._hide_btns()
            model = SongMiniCardListModel(
                create_reader(self._app.recently_played.list_songs()),
                fetch_cover_wrapper(self._app)
            )
            view = SongMiniCardListView(**self._view_options)
            view.setModel(model)
            view.play_song_needed.connect(self._app.playlist.play_model)
        delegate = SongMiniCardListDelegate(
            view,
            card_min_width=self.width() - self.width()//6,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
        )
        view.setItemDelegate(delegate)
        self._stacked_layout.addWidget(view)
        self._stacked_layout.setCurrentWidget(view)

    def _hide_btns(self):
        for btn in self._btns:
            btn.hide()

    def _show_btns(self):
        for btn in self._btns:
            btn.show()

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        # Draw shadow effect on the left side.
        painter.save()
        shadow_width = self._shadow_width
        rect = QRect(0, 0, shadow_width, self.height())
        gradient = QLinearGradient(rect.topRight(), rect.topLeft())
        gradient.setColorAt(0, acolor('black', 70))
        gradient.setColorAt(0.05, acolor('black', 60))
        gradient.setColorAt(0.1, acolor('black', 30))
        gradient.setColorAt(0.2, acolor('black', 5))
        gradient.setColorAt(1, acolor('black', 0))
        painter.setBrush(gradient)
        painter.drawRect(rect)
        painter.restore()

        # Draw a rect to fill the remain background.
        painter.setBrush(self.palette().color(QPalette.Base))
        painter.drawRect(shadow_width, 0, self.width()-shadow_width, self.height())

    def showEvent(self, e):
        super().showEvent(e)
        self.show_tab(self._tabbar.currentIndex())

    def eventFilter(self, obj, event):
        """
        Hide myself when the app is resized.
        """
        if obj is self._app and event.type() == QEvent.Resize:
            self.hide()
        return False


class PlaybackModeSwitch(TextButton):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self.update_text()
        self.clicked.connect(self.switch_playback_mode)
        self._app.playlist.playback_mode_changed.connect(
            self.on_playback_mode_changed, aioqueue=True)
        self.setToolTip('修改播放模式')

    def switch_playback_mode(self):
        playlist = self._app.playlist
        index = PlaybackModes.index(playlist.playback_mode)
        if index < len(PlaybackModes) - 1:
            new_index = index + 1
        else:
            new_index = 0
        playlist.playback_mode = PlaybackModes[new_index]

    def update_text(self):
        self.setText(PlaybackModeName[self._app.playlist.playback_mode])

    def on_playback_mode_changed(self, _):
        self.update_text()
