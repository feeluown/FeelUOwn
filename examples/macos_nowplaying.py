from Foundation import NSRunLoop, NSMutableDictionary, NSObject
from MediaPlayer import MPRemoteCommandCenter, MPNowPlayingInfoCenter
from MediaPlayer import (
    MPMediaItemPropertyTitle, MPMediaItemPropertyArtist,
    MPMusicPlaybackState, MPMusicPlaybackStatePlaying, MPMusicPlaybackStatePaused,
    MPNowPlayingInfoPropertyElapsedPlaybackTime, MPMediaItemPropertyPlaybackDuration
)


class NowPlaying:
    def __init__(self):
        self.cmd_center = MPRemoteCommandCenter.sharedCommandCenter()
        self.info_center = MPNowPlayingInfoCenter.defaultCenter()

        cmds = [
            self.cmd_center.togglePlayPauseCommand(),
            self.cmd_center.playCommand(),
            self.cmd_center.pauseCommand(),
        ]

        for cmd in cmds:
            cmd.addTargetWithHandler_(self._create_handler(cmd))

        self.update_info()

    def update_info(self):
        nowplaying_info = NSMutableDictionary.dictionary()
        nowplaying_info[MPMediaItemPropertyTitle] = "title"
        nowplaying_info[MPMediaItemPropertyArtist] = "artist"
        nowplaying_info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = 0
        nowplaying_info[MPMediaItemPropertyPlaybackDuration] = 100
        self.info_center.setNowPlayingInfo_(nowplaying_info)
        self.info_center.setPlaybackState_(MPMusicPlaybackStatePlaying)


    def _create_handler(self, cmd):

        def handle(event):
            if event.command() == self.cmd_center.pauseCommand():
                self.info_center.setPlaybackState_(MPMusicPlaybackStatePaused)
            elif event.command() == self.cmd_center.playCommand():
                self.info_center.setPlaybackState_(MPMusicPlaybackStatePlaying)
            return 0

        return handle


def runloop():
    """
    HELP: This function can't be called in non-main thread.
    """
    nowplaying = NowPlaying()
    NSRunLoop.mainRunLoop().run()


runloop()
