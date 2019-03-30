import io
import sys
import traceback
import json

from .base import AbstractHandler
from .helpers import ReturnMessage, ReturnStatus


class ExecHandler(AbstractHandler):
    cmds = 'exec'

    def handle(self, cmd, output_format):
        code = cmd.args[0]
        if output_format == "plain":
            output = io.StringIO()
            sys.stderr = output
            sys.stdout = output
        else:
            stdout = io.StringIO()
            stderr = io.StringIO()
            sys.stdout = stdout
            sys.stderr = stderr
        
        is_failed = False
        try:
            self.exec_(code)
        except Exception as e:
            is_failed = True
            traceback.print_exc()
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__

        if output_format == "plain":
            msg = output.getvalue()
        else:
            result = ReturnMessage(output_format=output_format)
            result.status = ReturnStatus.fail if is_failed else ReturnStatus.success
            result.data = {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
            msg = result.dumps()
        return msg

    def exec_(self, code):
        obj = compile(code, '<string>', 'exec')
        g = {
            'player': self.player
        }
        exec(obj, g, g)
