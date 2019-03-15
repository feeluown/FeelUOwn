import io
import sys
import traceback

from .base import AbstractHandler


class ExecHandler(AbstractHandler):
    cmds = 'exec'

    def handle(self, cmd):
        code = cmd.args[0]
        output = io.StringIO()
        sys.stderr = output
        sys.stdout = output
        try:
            self.exec_(code)
        except Exception as e:
            traceback.print_exc()
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
        msg = output.getvalue()
        return msg

    def exec_(self, code):
        obj = compile(code, '<string>', 'exec')
        g = {
            'player': self.player
        }
        exec(obj, g, g)
