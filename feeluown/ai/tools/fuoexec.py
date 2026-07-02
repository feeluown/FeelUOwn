import io
import sys
import traceback

from langchain.tools import tool

from feeluown.ai.tools.result import tool_error, tool_success
from feeluown.fuoexec import fuoexec


@tool
def fuoexec_execute(code: str) -> dict:
    """Execute Python code in FeelUOwn's fuoexec namespace.

    This is a powerful tool. Use it only when other dedicated tools cannot
    complete the requested operation.

    :param code: Python code to execute.
    """
    output = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = output
    sys.stderr = output
    try:
        obj = compile(code, "<ai-copilot>", "exec")
        fuoexec(obj)
    except Exception as e:  # noqa
        traceback.print_exc()
        return tool_error(
            "fuoexec_execute",
            type(e).__name__,
            str(e),
            data={"output": output.getvalue()},
        )
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return tool_success(
        "fuoexec_execute",
        data={"output": output.getvalue()},
    )


fuoexec_tools = [
    fuoexec_execute,
]
