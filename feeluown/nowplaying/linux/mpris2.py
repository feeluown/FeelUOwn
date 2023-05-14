# pylint: disable=import-error
import logging
import os

import dbus
import dbus.service

from feeluown.app import App
from feeluown.player import State, PlaylistShuffleMode, PlaylistRepeatMode


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
    'CanQuit': True,
    'CanRaise': True,
    'HasTrackList': False,
    'SupportedUriSchemes': ['http', 'file', 'fuo'],
    'SupportedMimeTypes': SupportedMimeTypes,
}, signature='sv')
RepeatModeLoopStatusMapping = {
    PlaylistRepeatMode.all: 'Playlist',
    PlaylistRepeatMode.one: 'Track',
    PlaylistRepeatMode.none: 'None',
}
LoopStatusRepeatModeMapping = {v: k for k, v in RepeatModeLoopStatusMapping.items()}


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


def to_dbus_metadata(metadata):
    if metadata:
        artists = metadata.get('artists', ['Unknown'])[:1]
    else:
        # make xesam:artist a one-element list to compat with KDE
        # KDE will not update artist field if the length>=1
        artists = ['']
    uri = metadata.get('uri', 'fuo://unknown/unknown/unknown')
    return dbus.Dictionary({
        # If there is no artist, we give a empty string in case mpris complains
        # 'ValueError: Unable to guess signature from an empty list'
        'xesam:artist': artists or [''],
        'xesam:url': uri,
        # trackid must be provided to make 'Seek' work.
        'mpris:trackid': f'/org/feeluown/FeelUOwn/{uri[6:]}',
        'mpris:artUrl': metadata.get('artwork', ''),
        'xesam:album': metadata.get('album', ''),
        'xesam:title': metadata.get('title', ''),
    }, signature='sv')


class Mpris2Service(dbus.service.Object):
    # pylint: disable=too-many-public-methods

    def __init__(self, app: App, bus):
        super().__init__(bus, ObjectPath)
        self._app = app

    def enable(self):
        # 根据 mpris2 规范, position 变化时，不需要发送 PropertiesChanged 信号。
        # audacious 的一个 issue 也证明了这个观点:
        #   https://redmine.audacious-media-player.org/issues/849
        #   这个 issue 主要是说频繁发送 PropertiesChanged 信号会导致
        #   GNOME 桌面消耗大量 CPU。
        self._app.player.seeked.connect(self.update_position)
        self._app.player.duration_changed.connect(self.update_duration)
        self._app.player.state_changed.connect(self.update_playback_status)
        self._app.playlist.playback_mode_changed.connect(self.update_playback_mode)
        self._app.player.metadata_changed.connect(self.update_song_props)

    def disable(self):
        pass

    def update_playback_status(self, state):
        status = to_dbus_playback_status(state)
        self.PropertiesChanged(PlayerInterface,
                               {'PlaybackStatus': status}, [])

    def update_playback_mode(self, _):
        props = {
            'LoopStatus': RepeatModeLoopStatusMapping[self._app.playlist.repeat_mode],
            'Shuffle': self._app.playlist.shuffle_mode is not PlaylistShuffleMode.off,
        }
        self.PropertiesChanged(PlayerInterface, props, [])

    def update_position(self, position):
        self.Seeked(to_dbus_position(position))

    def update_duration(self, duration):
        if duration <= 0:  # Duration can be 0 when media is changed.
            return
        length = to_dbus_position(duration or 0)
        metadata = to_dbus_metadata(self._app.player.current_metadata)
        metadata['mpris:length'] = length
        props = dbus.Dictionary({'Metadata': metadata})
        self.PropertiesChanged(PlayerInterface, props, [])

    def update_song_props(self, metadata):
        props = dbus.Dictionary({'Metadata': to_dbus_metadata(metadata)})
        self.PropertiesChanged(PlayerInterface, props, [])

    def get_player_properties(self):
        return dbus.Dictionary({
            'Metadata': to_dbus_metadata(self._app.player.current_metadata),
            'Rate': 1.0,
            'MinimumRate': 1.0,
            'MaximumRate': 1.0,
            'CanGoNext': True,
            'CanGoPrevious': True,
            'CanControl': True,
            'CanSeek': True,
            'CanPause': True,
            'CanPlay': True,
            'Position': to_dbus_position(self._app.player.position or 0),
            'LoopStatus': RepeatModeLoopStatusMapping[self._app.playlist.repeat_mode],
            'Shuffle': self._app.playlist.shuffle_mode is not PlaylistShuffleMode.off,
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
        elif prop == 'LoopStatus':
            self._app.playlist.repeat_mode = LoopStatusRepeatModeMapping[value]
        elif prop == 'Shuffle':
            shuffle_mode = PlaylistShuffleMode.songs if value else \
                PlaylistShuffleMode.off
            self._app.playlist.shuffle_mode = shuffle_mode
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
            f'The Foo object does not implement the {interface} interface'
        )

    @dbus.service.method(AppInterface, in_signature='', out_signature='')
    def Quit(self):
        self._app.exit()

    @dbus.service.method(AppInterface, in_signature='', out_signature='')
    def Raise(self):
        if self._app.has_gui:
            self._app.raise_()

    @dbus.service.method(dbus.INTROSPECTABLE_IFACE, in_signature='', out_signature='s')
    def Introspect(self):  # pylint: disable=arguments-differ
        current_dir_name = os.path.dirname(os.path.realpath(__file__))
        xml = os.path.join(current_dir_name, 'introspect.xml')
        with open(xml, 'r', encoding='utf-8') as f:
            contents = f.read()
        return contents
