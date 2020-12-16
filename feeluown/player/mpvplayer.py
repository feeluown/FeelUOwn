import locale
import logging

from feeluown.utils.utils import use_mpv_old

if use_mpv_old():
    from mpv_old import (
        MPV,
        MpvEventID,
        MpvEventEndFile,
        _mpv_set_property_string,
        _mpv_set_option_string,
        _mpv_client_api_version,
    )
else:
    from mpv import (
        MPV,
        MpvEventID,
        MpvEventEndFile,
        _mpv_set_property_string,
        _mpv_set_option_string,
        _mpv_client_api_version,
    )

from feeluown.utils.dispatch import Signal
from feeluown.media import Media
from .base_player import AbstractPlayer, State


logger = logging.getLogger(__name__)


class MpvPlayer(AbstractPlayer):
    """

    player will always play playlist current song. player will listening to
    playlist ``song_changed`` signal and change the current playback.

    todo: make me singleton
    """
    def __init__(self, audio_device=b'auto', winid=None, *args, **kwargs):
        super(MpvPlayer, self).__init__(*args, **kwargs)
        # https://github.com/cosven/FeelUOwn/issues/246
        locale.setlocale(locale.LC_NUMERIC, 'C')
        mpvkwargs = {}
        if winid is not None:
            mpvkwargs['wid'] = winid
        self._version = _mpv_client_api_version()

        # old version libmpv can use opengl-cb
        if self._version < (1, 107):
            mpvkwargs['vo'] = 'opengl-cb'
            self.use_opengl_cb = True
        else:
            self.use_opengl_cb = False

        # set log_handler if you want to debug
        # mpvkwargs['log_handler'] = self.__log_handler
        # mpvkwargs['msg_level'] = 'all=v'
        # the default version of libmpv on Ubuntu 18.04 is (1, 25)
        self._mpv = MPV(ytdl=False,
                        input_default_bindings=True,
                        input_vo_keyboard=True,
                        **mpvkwargs)
        _mpv_set_property_string(self._mpv.handle, b'audio-device', audio_device)
        # old version libmpv(for example: (1, 20)) should set option by using
        # _mpv_set_option_string, while newer version can use _mpv_set_property_string
        _mpv_set_option_string(self._mpv.handle, b'user-agent',
                               b'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

        #: if video_format changes to None, there is no video available
        self.video_format_changed = Signal()

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
        logger.debug('Player initialize finished.')

    def shutdown(self):
        self._mpv.terminate()

    def play(self, media, video=True):
        logger.debug("Player will play: '%s'", media)
        if isinstance(media, Media):
            media = media
        else:  # media is a url
            media = Media(media)
        self._set_http_headers(media.http_headers)
        url = media.url

        # Clear playlist before play next song,
        # otherwise, mpv will seek to the last position and play.
        self.media_about_to_changed.emit(self._current_media, media)
        self._mpv.playlist_clear()
        self._mpv.play(url)
        self._current_media = media
        self.media_changed.emit(media)

    def set_play_range(self, start=None, end=None):
        if self._version >= (1, 28):
            start_default, end_default = 'none', 'none'
        else:
            start_default, end_default = '0%', '100%'
        start = str(start) if start is not None else start_default
        end = str(end) if end is not None else end_default
        _mpv_set_option_string(self._mpv.handle, b'start', bytes(start, 'utf-8'))
        _mpv_set_option_string(self._mpv.handle, b'end', bytes(end, 'utf-8'))

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

    def _on_event(self, event):
        if event['event_id'] == MpvEventID.END_FILE:
            reason = event['event']['reason']
            logger.debug('Current song finished. reason: %d' % reason)
            if self.state != State.stopped and reason != MpvEventEndFile.ABORTED:
                self.media_finished.emit()

    def _set_http_headers(self, http_headers):
        if http_headers:
            headers = []
            for key, value in http_headers.items():
                headers.append("{}: {}".format(key, value))
            headers_text = ','.join(headers)
            headers_bytes = bytes(headers_text, 'utf-8')
            logger.info('play media with headers: %s', headers_text)
            _mpv_set_option_string(self._mpv.handle, b'http-header-fields',
                                   headers_bytes)
        else:
            _mpv_set_option_string(self._mpv.handle, b'http-header-fields',
                                   b'')

    def __log_handler(self, loglevel, component, message):
        print('[{}] {}: {}'.format(loglevel, component, message))
