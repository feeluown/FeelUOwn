from fuocore.protocol import ModelParser

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
    def __init__(self, library, player, playlist, live_lyric):
        self.library = library
        self.player = player
        self.playlist = playlist
        self.live_lyric = live_lyric
        self.model_parser = ModelParser(library)

    def handle(self, cmd, output_format):
        raise NotImplementedError
