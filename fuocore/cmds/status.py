from .base import AbstractHandler


class StatusHandler(AbstractHandler):
    cmds = 'status'

    def handle(self, cmd):
        return self._app
