# -*- coding: utf-8 -*-

from PyQt5.QtMultimedia import QMediaPlayer

import dbus
import dbus.service

from feeluown.logger import LOG
from feeluown.controller_api import ControllerApi


FEELUOWN_MPRIS_BUS_NAME = 'org.mpris.MediaPlayer2.feeluown'
MPRIS_OBJECT_PATH = '/org/mpris/MediaPlayer2'
MPRIS_MEDIAPLAYER_INTERFACE = 'org.mpris.MediaPlayer2'
MPRIS_MEDIAPLAYER_PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'


class MprisServer(dbus.service.Object):
    def __init__(self):
        bus = dbus.service.BusName(
            FEELUOWN_MPRIS_BUS_NAME,
            bus=dbus.SessionBus())
        super().__init__(bus, MPRIS_OBJECT_PATH)

        ControllerApi.player.positionChanged.connect(self._Seeked)
        ControllerApi.player.signal_player_media_changed.connect(
            self._update_song_base_props)
        ControllerApi.player.stateChanged.connect(
            self._update_playback_status)

        self._properties = dbus.Dictionary({
            'DesktopEntry': 'FeelUOwn',
            'Identity': 'feeluown',
            'CanQuit': False,
            'CanRaise': False,
            'HasTrackList': False,
        }, signature='sv')

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
            'LoopStatus': 'Playlist',
            'PlaybackStatus': 'Stopped',    # ['Stopped', 'Paused', 'Playing']
            'Volume': 1.0,
        }, signature='sv', variant_level=2)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Play(self):
        LOG.info('dbus: call play')
        ControllerApi.player.play()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Pause(self):
        LOG.info('dbus: call pause')
        ControllerApi.player.pause()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Next(self):
        LOG.info('dbus: call play_next')
        ControllerApi.player.play_next()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Previous(self):
        LOG.info('dbus: call play last')
        ControllerApi.player.play_last()

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='s', out_signature='')
    def OpenUri(self, Uri):
        LOG.info('dbus: call play open uri')

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='ox', out_signature='')
    def SetPosition(self, TrackId, Position):
        ControllerApi.player.setPosition(Position/1000)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def PlayPause(self):
        ControllerApi.player.play_or_pause()

    def _Seeked(self, position):
        self.Seeked(dbus.Int64(position*1000))
        self._player_properties['Position'] = dbus.Int64(position*1000)
        self.PropertiesChanged(
            MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
            {'Position': dbus.Int64(position*1000)},
            [])

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='x', out_signature='')
    def Seek(self, Offset):
        ControllerApi.player.setPosition(Offset/1000)

    @dbus.service.method(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         in_signature='', out_signature='')
    def Stop(self):
        ControllerApi.player.stop()

    @dbus.service.signal(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                         signature='x')
    def Seeked(self, Position):
        pass

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
        f = open('./introspect.xml')
        contents = f.read()
        f.close()
        return contents

    def _update_song_base_props(self, music_model):
        props = dbus.Dictionary({'Metadata': dbus.Dictionary({
            'xesam:artist':
                [artist['name'] for artist in music_model['artists']],
            'xesam:url': music_model['url'],
            'mpris:length': dbus.Int64(music_model['duration']*1000),
            'mpris:artUrl': music_model['album']['picUrl'],
            'xesam:album': music_model['album']['name'],
            'xesam:title': music_model['name'],
        }, signature='sv')}, signature='sv')
        self._player_properties.update(props)

        self.PropertiesChanged(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                               props, [])

    def _update_playback_status(self, playback_status):
        if playback_status == QMediaPlayer.StoppedState:
            status = self._player_properties['PlaybackStatus'] = 'Stopped'
        elif playback_status == QMediaPlayer.PausedState:
            status = self._player_properties['PlaybackStatus'] = 'Paused'
        else:
            status = self._player_properties['PlaybackStatus'] = 'Playing'

        self.PropertiesChanged(MPRIS_MEDIAPLAYER_PLAYER_INTERFACE,
                               {'PlaybackStatus': status}, [])


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget
    import dbus.mainloop.pyqt5

    dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    app = QApplication(sys.argv)
    w = QWidget()
    w.show()
    mpris = MprisServer()
    sys.exit(app.exec_())
