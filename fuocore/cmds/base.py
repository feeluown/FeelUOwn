cmd_handler_mapping = {}


class HandlerMeta(type):
    def __new__(cls, name, bases, attrs):
        klass = type.__new__(cls, name, bases, attrs)
        if 'cmds' in attrs:
            cmds = attrs['cmds']
            if isinstance(cmds, str):
                cmd_handler_mapping[cmds] = klass
            else:
                for cmd in cmds:
                    cmd_handler_mapping[cmd] = klass
        return klass


class AbstractHandler(metaclass=HandlerMeta):
    def __init__(self, app, library, player, playlist, live_lyric):
        self._app = app
        self.library = library
        self.player = player
        self.playlist = playlist
        self.live_lyric = live_lyric

    def handle(self, cmd):
        raise NotImplementedError
