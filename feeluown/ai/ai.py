from typing import Optional

from feeluown.app import App
from feeluown.ai.copilot import Copilot
from feeluown.ai.radio import AIRadioSession

# FIXME: Other packages should only import things from feeluown.ai
#  They should not import things from feeluown.ai.copilot or other inner moduels.


class AI:
    def __init__(self, app: App):
        self._app = app
        self._copilot = Copilot(self._app)
        self.radio = None

    def get_copilot(self):
        return self._copilot

    def get_active_radio(self) -> Optional["AIRadioSession"]:
        if self.radio is not None and self.radio.is_active:
            return self.radio
        return None

    def activate_radio(self, reset=True) -> AIRadioSession:
        """Activate AI Radio and return the active session."""
        active_radio = self.get_active_radio()
        if active_radio is not None:
            return active_radio

        radio = AIRadioSession(self._app)
        radio.activate(reset=reset)
        return radio

    def deactivate_radio(self) -> bool:
        """Deactivate AI Radio. Return True when a session was active."""
        radio = self.radio
        if radio is None:
            return False

        was_active = radio.is_active
        radio.deactivate()
        return was_active
