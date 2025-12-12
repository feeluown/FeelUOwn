from feeluown.app import App
from feeluown.ai.copilot import Copilot


# FIXME: Other packages should only import things from feeluown.ai
#  They should not import things from feeluown.ai.copilot or other inner moduels.


class AI:
    def __init__(self, app: App):
        self._app = app
        self._copilot = Copilot(self._app)

    def get_copilot(self):
        return self._copilot
