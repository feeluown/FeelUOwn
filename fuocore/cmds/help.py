from .base import AbstractHandler


class HelpHandler(AbstractHandler):
    cmds = 'help'

    def handle(self, cmd):
        return """
Available commands::

    search <string>  # search songs by <string>
    show fuo://xxx  # show xxx detail info
    play fuo://xxx/songs/yyy  # play yyy song
    list  # show player current playlist
    status  # show player status
    next  # play next song
    previous  # play previous song
    pause
    resume
    toggle

Watch live lyric::

    echo "sub topic.live_lyric" | nc host 23334
"""
