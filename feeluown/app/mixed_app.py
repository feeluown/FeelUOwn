from .server_app import ServerApp
from .gui_app import GuiApp


class MixedApp(ServerApp, GuiApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        super().initialize()

    def run(self):
        super().run()
