import asyncio
import logging

from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFontMetrics, QPainter
from PyQt5.QtWidgets import (
    QApplication, QLabel, QFrame, QHBoxLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QMenu,
)

from feeluown.library import ProviderFlags
from feeluown.utils import aio
from feeluown.excs import ProviderIOError
from feeluown.media import MediaType
from feeluown.player import PlaybackMode, State
from feeluown.gui.widgets.lyric import Window as LyricWindow
from feeluown.gui.helpers import async_run
from feeluown.widgets import TextButton
from feeluown.widgets.volume_button import VolumeButton
from feeluown.widgets.progress_slider import ProgressSlider
from feeluown.gui.widgets.labels import ProgressLabel, DurationLabel

logger = logging.getLogger(__name__)


class SongBriefLabel(QLabel):
    default_text = '...'

    def __init__(self, app):
        super().__init__(text=self.default_text, parent=None)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._app = app

        # TODO: we can create a label class that roll the text when
        # the text is longer than the label width
        self._timer = QTimer()
        self._txt = self._raw_text = self.default_text
        self._font_metrics = QFontMetrics(QApplication.font())
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
        # text's position, keep changing to make text roll
        self._pos = 0
        self._timer.timeout.connect(self.change_text_position)

        self._fetching_artists = False

    def change_text_position(self):
        if not self.parent().isVisible():
            self._timer.stop()
            self._pos = 0
            return
        if self._text_rect.width() + self._pos > 0:
            # control the speed of rolling
            self._pos -= 5
        else:
            self._pos = self.width()
        self.update()

    def setText(self, text):
        self._txt = self._raw_text = text
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
        self._pos = 0
        self.update()

    def enterEvent(self, event):
        # we do not compare text_rect with self_rect here because of
        # https://github.com/feeluown/FeelUOwn/pull/425#discussion_r536817226
        # TODO: find out why
        if self._txt != self._raw_text:
            # decrease to make rolling more fluent
            self._timer.start(150)

    def leaveEvent(self, event):
        self._timer.stop()
        self._pos = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QApplication.font())
        painter.setPen(self._app.palette().color(self._app.palette().Text))

        if self._timer.isActive():
            self._txt = self._raw_text
        else:
            self._txt = self._font_metrics.elidedText(
                self._raw_text, Qt.ElideRight, self.width())

        painter.drawText(
            QRect(self._pos, 0, self.width() - self._pos, self.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            self._txt
        )

    def contextMenuEvent(self, e):
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        menu.hovered.connect(self.on_action_hovered)
        artist_menu = menu.addMenu('查看歌手')
        album_action = menu.addAction('查看专辑')

        artist_menu.menuAction().setData({'artists': None, 'song': song})

        album_action.triggered.connect(
            lambda: aio.create_task(self._goto_album(song)))

        if self._app.library.check_flags_by_model(song, ProviderFlags.similar):
            similar_song_action = menu.addAction('相似歌曲')
            similar_song_action.triggered.connect(
                lambda: self._app.browser.goto(model=song, path='/similar'))
        if self._app.library.check_flags_by_model(song, ProviderFlags.hot_comments):
            song_comments_action = menu.addAction('歌曲评论')
            song_comments_action.triggered.connect(
                lambda: self._app.browser.goto(model=song, path='/hot_comments'))

        menu.exec(e.globalPos())

    async def _goto_album(self, song):
        album = await aio.run_in_executor(
            None, lambda: self._app.library.song_upgrade(song).album)
        self._app.browser.goto(model=album)

    def on_action_hovered(self, action):
        """
        Fetch song.artists when artists_action is hovered. If it is
        already fetched, ignore.
        """
        data = action.data()
        if data is None:  # submenu action
            return

        def artists_fetched_cb(future):
            self._fetching_artists = False
            artists = future.result()  # ignore the potential exception
            if artists:
                for artist in artists:
                    artist_action = action.menu().addAction(artist.name)
                    # create a closure to bind variable artist
                    artist_action.triggered.connect(
                        (lambda x: lambda: self._app.browser.goto(model=x))(artist))
            data['artists'] = artists or []
            action.setData(data)

        # the action is artists_action
        if 'artists' in data:
            # artists value has not been fetched
            if data['artists'] is None and self._fetching_artists is False:
                logger.debug('fetch song.artists for actions')
                song = data['song']
                self._fetching_artists = True
                task = aio.run_in_executor(
                    None, lambda: self._app.library.song_upgrade(song).artists)
                task.add_done_callback(artists_fetched_cb)


class PlayerControlPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        class IconButton(QPushButton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        self._playback_modes = list(PlaybackMode.__members__.values())
        self._pm_alias_map = {
            PlaybackMode.one_loop: '单曲循环',
            PlaybackMode.sequential: '顺序播放',
            PlaybackMode.loop: '循环播放',
            PlaybackMode.random: '随机播放',
        }

        # initialize sub widgets
        self._layout = QHBoxLayout(self)
        self.previous_btn = IconButton(self)
        self.pp_btn = IconButton(self)
        self.next_btn = IconButton(self)

        #: playback mode switch button
        self.pms_btn = TextButton(self)
        self.volume_btn = VolumeButton(self)
        self.playlist_btn = IconButton(parent=self)
        #: mark song as favorite button
        self.like_btn = QPushButton(self)
        self.mv_btn = TextButton('MV', self)
        self.lyric_btn = TextButton('词', self)
        self.download_btn = QPushButton(self)
        self.toggle_video_btn = TextButton('△', self)
        # toggle picture-in-picture button
        self.toggle_pip_btn = TextButton('◲', self)

        self.lyric_window = LyricWindow()
        self.lyric_window.hide()

        self.previous_btn.setObjectName('previous_btn')
        self.pp_btn.setObjectName('pp_btn')
        self.next_btn.setObjectName('next_btn')
        self.playlist_btn.setObjectName('playlist_btn')
        self.volume_btn.setObjectName('volume_btn')
        self.pms_btn.setObjectName('pms_btn')
        self.download_btn.setObjectName('download_btn')
        self.like_btn.setObjectName('like_btn')
        self.mv_btn.setObjectName('mv_btn')
        self.lyric_btn.setObjectName('lyric_btn')
        self.toggle_video_btn.setObjectName('toggle_video_btn')
        self.toggle_pip_btn.setObjectName('toggle_pip_btn')

        self.progress_slider = ProgressSlider(app=app, parent=self)

        self.pms_btn.setToolTip('修改播放模式')
        self.volume_btn.setToolTip('调整音量')
        self.playlist_btn.setToolTip('显示当前播放列表')

        self.mv_btn.setToolTip('播放 MV')
        self.download_btn.setToolTip('下载歌曲（未实现，欢迎 PR）')
        self.like_btn.setToolTip('收藏歌曲（未实现，欢迎 PR）')
        self.pp_btn.setCheckable(True)
        self.like_btn.setCheckable(True)
        self.download_btn.setCheckable(True)
        self.toggle_video_btn.hide()
        self.toggle_pip_btn.hide()

        self.song_title_label = SongBriefLabel(self._app)
        self.song_source_label = QLabel('歌曲来源', parent=self)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.duration_label = DurationLabel(app, parent=self)
        self.position_label = ProgressLabel(app, parent=self)

        # we should enable focus since we want to have shortcut keys
        self.setFocusPolicy(Qt.StrongFocus)
        self.song_source_label.setObjectName('song_source_label')

        self.next_btn.clicked.connect(self._app.playlist.next)
        self.previous_btn.clicked.connect(self._app.playlist.previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self.pms_btn.clicked.connect(self._switch_playback_mode)
        self.lyric_btn.clicked.connect(self._toggle_lyric_window)
        self.volume_btn.change_volume_needed.connect(
            lambda volume: setattr(self._app.player, 'volume', volume))

        player = self._app.player

        player.state_changed.connect(self._on_player_state_changed, aioqueue=True)
        player.playlist.playback_mode_changed.connect(
            self.on_playback_mode_changed, aioqueue=True)
        player.playlist.song_changed.connect(
            self.on_player_song_changed, aioqueue=True)
        player.media_changed.connect(
            self.on_player_media_changed, aioqueue=True)
        player.volume_changed.connect(self.volume_btn.on_volume_changed)
        self._app.live_lyric.sentence_changed.connect(self.lyric_window.set_sentence)
        self.lyric_window.play_previous_needed.connect(player.playlist.previous)
        self.lyric_window.play_next_needed.connect(player.playlist.next)

        self._update_pms_btn_text()
        self._setup_ui()

    def _setup_ui(self):
        # set widget layout
        self.song_source_label.setFixedHeight(20)
        self.progress_slider.setFixedHeight(20)  # half of parent height
        self.position_label.setFixedWidth(50)
        self.duration_label.setFixedWidth(50)
        # on macOS, we should set AlignVCenter flag
        self.position_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.like_btn.setFixedSize(15, 15)
        self.download_btn.setFixedSize(15, 15)
        self.mv_btn.setFixedHeight(16)
        self.lyric_btn.setFixedHeight(16)

        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._sub_layout = QVBoxLayout()
        self._sub_top_layout = QHBoxLayout()

        # add space to make top layout align with progress slider
        self._sub_top_layout.addSpacing(3)
        self._sub_top_layout.addWidget(self.song_source_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.song_title_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.like_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.mv_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.lyric_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.download_btn)
        self._sub_top_layout.addSpacing(3)

        self._sub_layout.addSpacing(3)
        self._sub_layout.addLayout(self._sub_top_layout)
        self._sub_layout.addWidget(self.progress_slider)

        self._layout.addSpacing(20)
        self._layout.addWidget(self.previous_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.pp_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.next_btn)
        self._layout.addSpacing(26)
        self._layout.addWidget(self.volume_btn)
        # 18 = 200(left_panel_width) - 4 * 30(btn) - 20 - 8 - 8 -26
        self._layout.addSpacing(18)
        self._layout.addStretch(0)
        self._layout.addWidget(self.position_label)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._sub_layout)
        self._layout.setStretchFactor(self._sub_layout, 1)
        self._layout.addSpacing(7)
        self._layout.addWidget(self.duration_label)
        self._layout.addStretch(0)
        self._layout.addSpacing(18)
        self._layout.addWidget(self.pms_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.playlist_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_video_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_pip_btn)
        self._layout.addSpacing(18)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def _switch_playback_mode(self):
        playlist = self._app.player.playlist
        pm_total = len(self._playback_modes)
        pm_idx = self._playback_modes.index(playlist.playback_mode)
        if pm_idx < pm_total - 1:
            pm_idx += 1
        else:
            pm_idx = 0
        playlist.playback_mode = self._playback_modes[pm_idx]

    def on_playback_mode_changed(self, playback_mode):
        self._update_pms_btn_text()

    def _update_pms_btn_text(self):
        playback_mode = self._app.player.playlist.playback_mode
        alias = self._pm_alias_map[playback_mode]
        self.pms_btn.setText(alias)

    def on_player_song_changed(self, song):
        if song is None:
            self.song_source_label.setText('歌曲来源')
            self.song_title_label.setText('No song is playing.')
            return
        source_name_map = {p.identifier: p.name
                           for p in self._app.library.list()}
        text = '{} - {}'.format(song.title_display, song.artists_name_display)
        # width -> three button + source label + text <= progress slider
        # three button: 63, source label: 150
        source_name = source_name_map.get(song.source, song.source)
        self.song_source_label.setText(source_name)
        self.song_title_label.setText(text)
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_mv_btn_status(song))

    def on_player_media_changed(self, media):
        if media is not None and media.type_ == MediaType.audio:
            metadata = media.metadata
            if metadata.bitrate:
                text = self.song_source_label.text()
                bitrate_text = str(metadata.bitrate) + 'kbps'
                self.song_source_label.setText(
                    '{} - {}'.format(text, bitrate_text))

    async def update_mv_btn_status(self, song):
        song = self._app.library.cast_model_to_v1(song)
        try:
            mv = await async_run(lambda: song.mv)
        except ProviderIOError:
            logger.exception('fetch song mv info failed')
            self.mv_btn.setEnabled(False)
        else:
            if mv:
                self.mv_btn.setToolTip(mv.name)
                self.mv_btn.setEnabled(True)
            else:
                self.mv_btn.setEnabled(False)

    def _on_player_state_changed(self, state):
        self.pp_btn.setChecked(state == State.playing)

    def _toggle_lyric_window(self):
        if self.lyric_window.isVisible():
            self.lyric_window.hide()
        else:
            self.lyric_window.show()


class TopPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)
        self.setObjectName('top_panel')

        self.setFixedHeight(60)

        self._layout.addWidget(self.pc_panel)
