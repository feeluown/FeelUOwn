from langchain.tools import tool, ToolRuntime

from feeluown.ai.tools.result import tool_bool_result, tool_error, tool_success


def _get_active_ai_radio(runtime: ToolRuntime):
    ai = runtime.context.app.ai
    if ai is None:
        return None
    return ai.get_active_radio()


def _ai_radio_inactive_result():
    return tool_error(
        "ai_radio_get_state",
        "AI_RADIO_INACTIVE",
        message="AI Radio is not active.",
        data={"active": False, "candidates": [], "candidate_count": 0},
    )


def _ai_radio_unavailable_result():
    return tool_error(
        "ai_radio_get_state",
        "AI_UNAVAILABLE",
        message="AI is not available.",
        data={"active": False, "candidates": [], "candidate_count": 0},
    )


@tool
def ai_radio_activate(runtime: ToolRuntime, reset: bool = True) -> dict:
    """Activate AI Radio.

    This switches the playlist into FM mode and lets the current AI radio
    session provide future candidate songs.

    :param reset: Whether to reset the current playlist when entering FM mode.
    """
    app = runtime.context.app
    if app.ai is None:
        return tool_bool_result(
            "ai_radio_activate",
            False,
            "AI_UNAVAILABLE",
            "AI is not available.",
        )

    radio = app.ai.get_active_radio()
    if radio is not None:
        return tool_success(
            "ai_radio_activate",
            data={"success": True, "already_active": True},
        )

    app.ai.activate_radio(reset=reset)
    return tool_success(
        "ai_radio_activate",
        data={"success": True, "already_active": False},
    )


@tool
def ai_radio_deactivate(runtime: ToolRuntime) -> dict:
    """Deactivate AI Radio and leave playlist FM mode."""
    app = runtime.context.app
    if app.ai is None:
        return tool_bool_result(
            "ai_radio_deactivate",
            False,
            "AI_UNAVAILABLE",
            "AI is not available.",
        )
    was_active = app.ai.deactivate_radio()
    return tool_success(
        "ai_radio_deactivate",
        data={"success": True, "was_active": was_active},
    )


@tool
def ai_radio_get_state(runtime: ToolRuntime) -> dict:
    """Get current AI radio state."""
    if runtime.context.app.ai is None:
        return _ai_radio_unavailable_result()
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return _ai_radio_inactive_result()
    return tool_success("ai_radio_get_state", data=radio.get_state_for_ai())


@tool
def ai_radio_update_preferences(
    runtime: ToolRuntime,
    preferences: list[str] | None = None,
    avoidances: list[str] | None = None,
    reason: str = "",
) -> dict:
    """Update current-session AI radio preferences.

    Use this when the user gives feedback that should affect future automatic
    AI radio recommendations.

    :param preferences: Musical traits the user wants more of.
    :param avoidances: Musical traits the user wants less of.
    :param reason: Short reason derived from the user's feedback.
    """
    radio = _get_active_ai_radio(runtime)
    if radio is None:
        return tool_bool_result(
            "ai_radio_update_preferences",
            False,
            "AI_RADIO_INACTIVE",
            "AI Radio is not active.",
        )
    success = radio.update_preferences(
        preferences=preferences or [],
        avoidances=avoidances or [],
        reason=reason,
    )
    return tool_bool_result("ai_radio_update_preferences", success)


ai_radio_tools = [
    ai_radio_activate,
    ai_radio_deactivate,
    ai_radio_get_state,
    ai_radio_update_preferences,
]
