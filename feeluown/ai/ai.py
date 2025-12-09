from feeluown.app import App
from feeluown.ai.radio import AIRadio


# FIXME: Other packages should only import things from feeluown.ai
#  They should not import things from feeluown.ai.radio or other inner moduels.


class AI:
    def __init__(self, app: App):
        self._app = app
        self._radio = AIRadio(self._app)

    def get_radio(self):
        return self._radio
