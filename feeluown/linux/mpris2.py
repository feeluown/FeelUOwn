import logging
import os

import dbus
import dbus.service
from fuocore.player import State


SupportedMimeTypes = ['audio/aac',
                      'audio/m4a',
                      'audio/mp3',
                      'audio/wav',
                      'audio/wma',
                      'audio/x-ape',
                      'audio/x-flac',
                      'audio/x-ogg',
                      'audio/x-oggflac',
                      'audio/x-vorbis']
FEELUOWN_MPRIS_BUS_NAME = 'org.mpris.MediaPlayer2.feeluown'
MPRIS_OBJECT_PATH = '/org/mpris/MediaPlayer2'
MPRIS_MEDIAPLAYER_INTERFACE = 'org.mpris.MediaPlayer2'
MPRIS_MEDIAPLAYER_PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'


logger = logging.getLogger(__name__)


def to_dbus_position(p): return dbus.Int64(p * 1000 * 1000)


def to_fuo_position(p): return p / 1000 / 1000


def to_track_id(model):
    return '/com/feeluown/{}/songs/{}'.format(
        model.source, model.identifier)


class Mpris2Service(dbus.service.Object):
    def __init__(self, app):
        bus = dbus.service.BusName(
            FEELUOWN_MPRIS_BUS_NAME,
            bus=dbus.SessionBus())
        super().__init__(bus, MPRIS_OBJECT_PATH)
        self._app = app

        self._properties = dbus.Dictionary({
            'DesktopEntry': 'FeelUOwn',
            'Identity': 'feeluown',
            'CanQuit': False,
            'CanRaise': False,
            'HasTrackList': False,
            'SupportedUriSchemes': ['http', 'file', 'smb'],
            'SupportedMimeTypes': SupportedMimeTypes,
        }, signature='sv')

        self._current_position = 0

        self._player_properties = dbus.Dictionary({
            'Metadata': dbus.Dictionary({
                'mpris:length': dbus.Int64(0),
                'mpris:artUrl': '',
                'xesam:artist': ['None'],
                'xesam:title': 'None',
                'xesam:url': '',
                'xesam:album': 'None'
            }, signature='sv', variant_level=1),
            'Rate': 1.0,
            'MinimumRate': 1.0,
            'MaximumRate': 1.0,
            'CanGoNext': True,
            'CanGoPrevious': True,
            'CanControl': True,
            'CanSeek': True,
            'CanPause': True,
            'CanPlay': True,
            'Position': dbus.Int64(0),
            # 'LoopStatus': 'Playlist',
            'PlaybackStatus': 'Stopped',    # ['Stopped', 'Paused', 'Playing']
            'Volume': 1.0,
        }, signature='sv', variant_level=2)

    def enable(self):
        self._app.player.position_changed.connect(self.update_position)
        self._app.player.state_changed.connect(self.update_playback_status)
        self._app.playlist.song_changed.connect(self.async_update_song_props)

    def disable(self):
        pass

    def update_playback_status(self, playback_status):
        if playback_status == State.stopped:
            status = self._player_properties['PlaybackStatus'] = 'Stopped'
        elif playback_status == State.paused:
            status = self._player_properties['PlaybackStatus'] = 'Paused'
        else:
            status = self._player_properties['PlaybackStatus'] = 'Playing'

        self.PropertiesChanged(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                               {'PlaybackStatus': status}, [])

    def update_position(self, position):
        # 根据 mpris2 规范, position 变化时，不需要发送 PropertiesChanged 信号。
        # audacious 的一个 issue 也证明了这个观点:
        #
        #   https://redmine.audacious-media-player.org/issues/849
        #   这个 issue 主要是说频繁发送 PropertiesChanged 信号会导致
        #   GNOME 桌面消耗大量 CPU。
        #
        # TODO: 由于目前 feeluown 播放器并没有提供 seeked 相关的信号，
        # 所以我们这里通过一个 HACK 来决定是否发送 seeked 信号。
        if position is None:
            return
        dbus_position = to_dbus_position(position)
        old_position = self._player_properties['Position']
        self._player_properties['Position'] = dbus_position

        # 如果时间差 1s 以上，我们认为这个 position 变化是由用户手动 seek 产生的
        # 根据目前观察，正常情况下，position 的变化差值是几百毫秒
        if abs(dbus_position - old_position) >= 1 * 1000 * 1000:
            self.Seeked(dbus_position)

    def async_update_song_props(self, song):
        task_spec = self._app.task_mgr.get_or_create('mpris2-update-property')
        task_spec.bind_blocking_io(self._update_song_props, song)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Play(self):
        logger.info('dbus: call play')
        self._app.player.resume()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Pause(self):
        logger.info('dbus: call pause')
        self._app.player.pause()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Next(self):
        logger.info('dbus: call play_next')
        self._app.player.play_next()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Previous(self):
        logger.info('dbus: call play last')
        self._app.player.play_previous()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='s', out_signature='')
    def OpenUri(self, Uri):
        logger.info('dbus: call play open uri')

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='ox', out_signature='')
    def SetPosition(self, TrackId, Position):
        logger.info('dbus: set position')
        self._app.player.position = to_fuo_position(Position)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def PlayPause(self):
        logger.info('dbus: call playpause')
        self._app.player.toggle()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='x', out_signature='')
    def Seek(self, Offset):
        self._app.player.position = to_fuo_position(Offset)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Stop(self):
        self._app.player.stop()

    @dbus.service.signal(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         signature='x')
    def Seeked(self, Position):
        logger.info('dbus: send seeked signal')

    @dbus.service.signal(dbus.PROPERTIES_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties=[]):
        pass

    @dbus.service.method(dbus.PROPERTIES_IFACE,
                         in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        return self.GetAll(interface)[prop]

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        self._player_properties[prop] = value
        if prop == 'Volume':
            self._app.player.volume = int(100 * value)

    @dbus.service.method(dbus.PROPERTIES_IFACE,
                         in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == MPRIS_MEDIAPLAYER_PLAYER_INTERFACE:
            return self._player_properties
        elif interface == MPRIS_MEDIAPLAYER_INTERFACE:
            return self._properties
        else:
            raise dbus.exceptions.DBusException(
                'com.example.UnknownInterface',
                'The Foo object does not implement the %s interface'
                % interface
            )

    @dbus.service.method(MPRIS_MEDIAPLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Quit(self):
        pass

    @dbus.service.method(dbus.INTROSPECTABLE_IFACE,
                         in_signature='', out_signature='s')
    def Introspect(self):
        current_dir_name = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir_name, 'introspect.xml'), 'r') as f:
            contents = f.read()
        return contents

    def _update_song_props(self, song):
        """
        此函数可能会涉及部分网络请求，目前我们将它放在 asyncio
        executor 中执行。
        """
        if song is None:
            return
        cover = ''
        if song.album:
            cover = song.album.cover or ''
        title = song.title
        artist = [', '.join((e.name for e in song.artists))] or ['Unknown']
        props = dbus.Dictionary({
            'Metadata': dbus.Dictionary({
                # make xesam:artist a one-element list to compat with KDE
                # KDE will not update artist field if the length>=2
                'xesam:artist': artist,
                'xesam:url': song.url,
                'mpris:length': dbus.Int64(song.duration*1000),
                'mpris:trackid': to_track_id(song),
                'mpris:artUrl': cover,
                'xesam:album': song.album_name,
                'xesam:title': title,
            }, signature='sv'),
            'Position': dbus.Int64(0),
        }, signature='sv')
        self._player_properties.update(props)
        self.PropertiesChanged(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                               props, [])
