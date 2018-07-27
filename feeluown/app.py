class App(object):
    CLIMode = 0x0001
    GUIMode = 0x0010

    mode = 0x0000

    def __init__(self, player, library):
        self.player = player
        self.playlist = player.playlist
        self.library = library
