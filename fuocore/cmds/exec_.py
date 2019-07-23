import io
import sys
import traceback

from feeluown.fuoexec import fuoexec
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
        except:  # noqa: E722
            traceback.print_exc()
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
        msg = output.getvalue()
        return msg

    def exec_(self, code):
        obj = compile(code, '<string>', 'exec')
        fuoexec(obj)
