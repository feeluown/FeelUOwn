from fuocore.player import PlaybackMode, State

from .base import AbstractHandler
from .helpers import show_song


class StatusHandler(AbstractHandler):
    cmds = 'status'

    def handle(self, cmd):
        player = self.player
        playlist = self.playlist
        live_lyric = self.live_lyric
        repeat = int(playlist.playback_mode in
                     (PlaybackMode.one_loop, PlaybackMode.loop))
        random = int(playlist.playback_mode == PlaybackMode.random)
        msgs = [
            'repeat:    {}'.format(repeat),
            'random:    {}'.format(random),
            'volume:    {}'.format(player.volume),
            'state:     {}'.format(player.state.name),
        ]
        if player.state in (State.playing, State.paused) and \
           player.current_song is not None:
            msgs += [
                'duration:  {}'.format(player.duration),
                'position:  {}'.format(player.position),
                'song:      {}'.format(show_song(player.current_song, brief=True, fetch=True)),  # noqa
                'lyric-s:   {}'.format(live_lyric.current_sentence),
            ]
        return '\n'.join(msgs)
