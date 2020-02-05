import locale
import logging
import warnings

from mpv import (
    MPV,
    MpvEventID,
    MpvEventEndFile,
    _mpv_set_property_string,
)

from fuocore.dispatch import Signal
from fuocore.media import Media
from fuocore.player import AbstractPlayer, State, PlaybackMode


logger = logging.getLogger(__name__)


class MpvPlayer(AbstractPlayer):
    """

    player will always play playlist current song. player will listening to
    playlist ``song_changed`` signal and change the current playback.

    TODO: make me singleton
    """
    def __init__(self, audio_device=b'auto', winid=None, *args, **kwargs):
        super(MpvPlayer, self).__init__(*args, **kwargs)
        # https://github.com/cosven/FeelUOwn/issues/246
        locale.setlocale(locale.LC_NUMERIC, 'C')
        mpvkwargs = {}
        if winid is not None:
            mpvkwargs['wid'] = winid
        mpvkwargs['vo'] = 'opengl-cb'
        # set log_handler if you want to debug
        # mpvkwargs['log_handler'] = self.__log_handler
        # mpvkwargs['msg_level'] = 'all=v'
        self._mpv = MPV(ytdl=True,
                        input_default_bindings=True,
                        input_vo_keyboard=True,
                        **mpvkwargs)
        _mpv_set_property_string(self._mpv.handle, b'audio-device', audio_device)

        # TODO: 之后可以考虑将这个属性加入到 AbstractPlayer 中
        self.video_format_changed = Signal()

    def initialize(self):
        self._mpv.observe_property(
            'time-pos',
            lambda name, position: self._on_position_changed(position)
        )
        self._mpv.observe_property(
            'duration',
            lambda name, duration: self._on_duration_changed(duration)
        )
        self._mpv.observe_property(
            'video-format',
            lambda name, vformat: self._on_video_format_changed(vformat)
        )
        # self._mpv.register_event_callback(lambda event: self._on_event(event))
        self._mpv._event_callbacks.append(self._on_event)
        self._playlist.song_changed.connect(self._on_song_changed)
        self.song_finished.connect(self._on_song_finished)
        logger.info('Player initialize finished.')

    def shutdown(self):
        self._mpv.terminate()

    def play(self, media, video=True):
        # NOTE - API DESGIN: we should return None, see
        # QMediaPlayer API reference for more details.

        logger.debug("Player will play: '%s'", media)

        if video:
            # FIXME: for some property, we need to set via setattr, however,
            #  some need to be set via _mpv_set_property_string
            self._mpv.handle.vid = b'auto'
            # it seems that ytdl will auto choose the default format
            #  if we set ytdl-format to ''
            _mpv_set_property_string(self._mpv.handle, b'ytdl-format', b'')
        else:
            # set vid to no and ytdl-format to bestaudio/best
            # see https://mpv.io/manual/stable/#options-vid for more details
            self._mpv.handle.vid = b'no'
            _mpv_set_property_string(self._mpv.handle, b'ytdl-format', b'bestaudio/best')

        if isinstance(media, Media):
            media = media
        else:  # media is a url
            media = Media(media)
        url = media.url

        # Clear playlist before play next song,
        # otherwise, mpv will seek to the last position and play.
        self._mpv.playlist_clear()
        self._mpv.play(url)
        self._mpv.pause = False
        self.state = State.playing
        self._current_media = media
        # TODO: we will emit a media object
        self.media_changed.emit(media)

    def prepare_media(self, song, done_cb=None):
        if song.meta.support_multi_quality:
            media, quality = song.select_media('hq<>')
        else:
            media = song.url
        media = Media(media) if media else None
        if done_cb is not None:
            done_cb(media)
        return media

    def play_song(self, song):
        """播放指定歌曲

        如果目标歌曲与当前歌曲不相同，则修改播放列表当前歌曲，
        播放列表会发出 song_changed 信号，player 监听到信号后调用 play 方法，
        到那时才会真正的播放新的歌曲。如果和当前播放歌曲相同，则忽略。

        .. note::

            调用方不应该直接调用 playlist.current_song = song 来切换歌曲
        """
        if song is not None and song == self.current_song:
            logger.warning('The song is already under playing.')
        else:
            self._playlist.current_song = song

    def play_songs(self, songs):
        """(alpha) play list of songs"""
        self.playlist.init_from(songs)
        self.play_next()

    def play_next(self):
        """播放下一首歌曲

        .. note::

            这里不能使用 ``play_song(playlist.next_song)`` 方法来切换歌曲，
            ``play_song`` 和 ``playlist.current_song = song`` 是有区别的。
        """
        warnings.warn('use playlist.next instead, this will be removed on 3.4')
        self.playlist.next()

    def play_previous(self):
        warnings.warn('use playlist.previous instead, this will be removed on 3.4')
        self.playlist.previous()

    def replay(self):
        self.playlist.current_song = self.current_song

    def resume(self):
        self._mpv.pause = False
        self.state = State.playing

    def pause(self):
        self._mpv.pause = True
        self.state = State.paused

    def toggle(self):
        self._mpv.pause = not self._mpv.pause
        if self._mpv.pause:
            self.state = State.paused
        else:
            self.state = State.playing

    def stop(self):
        self._mpv.pause = True
        self.state = State.stopped
        self._current_media = None
        self._mpv.playlist_clear()
        logger.info('Player stopped.')

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        if self._current_media:
            self._mpv.seek(position, reference='absolute')
            self._position = position
        else:
            logger.warn("can't set position when current media is empty")

    @AbstractPlayer.volume.setter
    def volume(self, value):
        super(MpvPlayer, MpvPlayer).volume.__set__(self, value)
        self._mpv.volume = self.volume

    @property
    def video_format(self):
        return self._video_format

    @video_format.setter
    def video_format(self, vformat):
        self._video_format = vformat
        self.video_format_changed.emit(vformat)

    def _on_position_changed(self, position):
        self._position = position
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration):
        """listening to mpv duration change event"""
        logger.debug('Player receive duration changed signal')
        self.duration = duration

    def _on_video_format_changed(self, vformat):
        self.video_format = vformat

    def _on_song_changed(self, song):
        """播放列表 current_song 发生变化后的回调

        判断变化后的歌曲是否有效的，有效则播放，否则将它标记为无效歌曲。
        如果变化后的歌曲是 None，则停止播放。
        """
        def prepare_callback(media):
            if media is not None:
                self.play(media)
            else:
                self._playlist.mark_as_bad(song)
                self.play_next()

        if song is not None:
            self.prepare_media(song, done_cb=prepare_callback)
        else:
            self.stop()

    def _on_event(self, event):
        if event['event_id'] == MpvEventID.END_FILE:
            reason = event['event']['reason']
            logger.debug('Current song finished. reason: %d' % reason)
            if self.state != State.stopped and reason != MpvEventEndFile.ABORTED:
                self.song_finished.emit()

    def _on_song_finished(self):
        if self._playlist.playback_mode == PlaybackMode.one_loop:
            self.replay()
        else:
            self.play_next()

    def __log_handler(self, loglevel, component, message):
        print('[{}] {}: {}'.format(loglevel, component, message))
