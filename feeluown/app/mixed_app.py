from .server_app import ServerApp
from .gui_app import GuiApp


class MixedApp(ServerApp, GuiApp):
    def __init__(self, config):
        super().__init__(config)

    def initialize(self):
        super().initialize()

    def run(self):
        super().run()
