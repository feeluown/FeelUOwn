class App(object):
    CliMode = 0x0001
    GuiMode = 0x0010

    mode = 0x0000

    def __init__(self, player, library, pubsub_gateway):
        self.player = player
        self.playlist = player.playlist
        self.library = library
        self.pubsub_gateway = pubsub_gateway
