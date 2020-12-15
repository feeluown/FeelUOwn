import logging
import os

import dbus
import dbus.service
from feeluown.player import State


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
BusName = 'org.mpris.MediaPlayer2.feeluown'
ObjectPath = '/org/mpris/MediaPlayer2'
AppInterface = 'org.mpris.MediaPlayer2'
PlayerInterface = 'org.mpris.MediaPlayer2.Player'
AppProperties = dbus.Dictionary({
    'DesktopEntry': 'FeelUOwn',
    'Identity': 'feeluown',
    'CanQuit': False,
    'CanRaise': False,
    'HasTrackList': False,
    'SupportedUriSchemes': ['http', 'file', 'smb'],
    'SupportedMimeTypes': SupportedMimeTypes,
}, signature='sv')


logger = logging.getLogger(__name__)


def to_dbus_position(p):
    return dbus.Int64(p * 1000 * 1000)


def to_fuo_position(p):
    return p / 1000 / 1000


def to_dbus_volume(volume):
    return round(volume / 100, 1)


def to_fuo_volume(volume):
    return int(volume * 100)


def to_dbus_playback_status(state):
    if state == State.stopped:
        status = 'Stopped'
    elif state == State.paused:
        status = 'Paused'
    else:
        status = 'Playing'
    return status


def to_track_id(model):
    return '/com/feeluown/{}/songs/{}'.format(
        model.source, model.identifier)


class Mpris2Service(dbus.service.Object):
    def __init__(self, app, bus):
        super().__init__(bus, ObjectPath)
        self._app = app
        self._metadata = dbus.Dictionary({}, signature='sv', variant_level=1)
        self._old_position = dbus.Int64(0)

    def enable(self):
        self._app.player.position_changed.connect(self.update_position)
        self._app.player.state_changed.connect(self.update_playback_status)
        self._app.playlist.song_changed.connect(self.async_update_song_props)

    def disable(self):
        pass

    def update_playback_status(self, state):
        status = to_dbus_playback_status(state)
        self.PropertiesChanged(PlayerInterface,
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
        old_position = self._old_position
        self._old_position = dbus_position = to_dbus_position(position)

        # 如果时间差 1s 以上，我们认为这个 position 变化是由用户手动 seek 产生的
        # 根据目前观察，正常情况下，position 的变化差值是几百毫秒
        if abs(dbus_position - old_position) >= 1 * 1000 * 1000:
            self.Seeked(dbus_position)

    def async_update_song_props(self, song):
        task_spec = self._app.task_mgr.get_or_create('mpris2-update-property')
        task_spec.bind_blocking_io(self._update_song_props, song)

    def _update_song_props(self, song):
        artist = [', '.join((e.name for e in song.artists))] or ['Unknown']
        self._metadata.update(dbus.Dictionary({
            # make xesam:artist a one-element list to compat with KDE
            # KDE will not update artist field if the length>=2
            'xesam:artist': artist,
            'xesam:url': song.url,
            'mpris:length': dbus.Int64(song.duration*1000),
            'mpris:trackid': to_track_id(song),
            'mpris:artUrl': (song.album.cover if song.album else '') or '',
            'xesam:album': song.album_name,
            'xesam:title': song.title,
        }, signature='sv'))
        changed_properties = dbus.Dictionary({'Metadata': self._metadata})
        self.PropertiesChanged(PlayerInterface, changed_properties, [])

    def get_player_properties(self):
        return dbus.Dictionary({
            'Metadata': self._metadata,
            'Rate': 1.0,
            'MinimumRate': 1.0,
            'MaximumRate': 1.0,
            'CanGoNext': True,
            'CanGoPrevious': True,
            'CanControl': True,
            'CanSeek': True,
            'CanPause': True,
            'CanPlay': True,
            'Position': self._old_position,
            # 'LoopStatus': 'Playlist',
            'PlaybackStatus': to_dbus_playback_status(self._app.player.state),
            'Volume': to_dbus_volume(self._app.player.volume),
        }, signature='sv', variant_level=2)

    # ##########################
    # implement mpris2 interface
    # ##########################
    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def Play(self):
        self._app.player.resume()

    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def Pause(self):
        self._app.player.pause()

    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def Next(self):
        self._app.playlist.next()

    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def Previous(self):
        self._app.playlist.previous()

    @dbus.service.method(PlayerInterface, in_signature='s', out_signature='')
    def OpenUri(self, Uri):
        pass

    @dbus.service.method(PlayerInterface, in_signature='ox', out_signature='')
    def SetPosition(self, TrackId, Position):
        self._app.player.position = to_fuo_position(Position)

    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def PlayPause(self):
        self._app.player.toggle()

    @dbus.service.method(PlayerInterface, in_signature='x', out_signature='')
    def Seek(self, Offset):
        self._app.player.position = to_fuo_position(Offset)

    @dbus.service.method(PlayerInterface, in_signature='', out_signature='')
    def Stop(self):
        self._app.player.stop()

    @dbus.service.signal(PlayerInterface, signature='x')
    def Seeked(self, Position):
        pass

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties=None):
        pass

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        return self.GetAll(interface)[prop]

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        if prop == 'Volume':
            self._app.player.volume = to_fuo_volume(value)
        else:
            logger.info("mpris wants to set %s to %s", prop, value)

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == PlayerInterface:
            props = self.get_player_properties()
            return props
        if interface == AppInterface:
            return AppProperties
        raise dbus.exceptions.DBusException(
            'com.example.UnknownInterface',
            'The Foo object does not implement the %s interface'
            % interface
        )

    @dbus.service.method(AppInterface, in_signature='', out_signature='')
    def Quit(self):
        pass

    @dbus.service.method(dbus.INTROSPECTABLE_IFACE, in_signature='', out_signature='s')
    def Introspect(self):
        current_dir_name = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir_name, 'introspect.xml'), 'r') as f:
            contents = f.read()
        return contents
