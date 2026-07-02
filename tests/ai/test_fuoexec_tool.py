from feeluown.ai.tools.fuoexec import fuoexec_execute
from feeluown.fuoexec.fuoexec import fuoexec_get_globals


def test_fuoexec_execute_tool_runs_code_in_fuoexec_namespace():
    globals_backup = fuoexec_get_globals().copy()
    try:
        result = fuoexec_execute.func(
            code="ai_tool_value = 42\nprint(ai_tool_value)"
        )

        assert result["ok"] is True
        assert result["action"] == "fuoexec_execute"
        assert result["data"]["output"] == "42\n"
        assert fuoexec_get_globals()["ai_tool_value"] == 42
    finally:
        fuoexec_get_globals().clear()
        fuoexec_get_globals().update(globals_backup)


def test_fuoexec_execute_tool_returns_error_with_traceback():
    result = fuoexec_execute.func(code="raise RuntimeError('boom')")

    assert result["ok"] is False
    assert result["action"] == "fuoexec_execute"
    assert result["error"]["code"] == "RuntimeError"
    assert result["error"]["message"] == "boom"
    assert "Traceback" in result["data"]["output"]
