from .cmd import Cmd
from .base import AbstractHandler


class SetHandler(AbstractHandler):
    cmds = ('set', )

    def handle(self, cmd: Cmd):
        assert self.session is not None
        options = cmd.options

        for key, value in options.items():
            # Treat None as the default value.
            # TODO: use a more meaningful default value.
            if value is not None:
                setattr(self.session.options, key, value)
