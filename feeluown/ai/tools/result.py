from dataclasses import dataclass, field


@dataclass
class ToolResult:
    ok: bool
    action: str
    message: str = ""
    data: dict = field(default_factory=dict)
    error: dict | None = None

    def to_dict(self):
        return {
            "ok": self.ok,
            "action": self.action,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }


def tool_success(action: str, data: dict | None = None, message: str = ""):
    return ToolResult(
        ok=True,
        action=action,
        message=message,
        data=data or {},
        error=None,
    ).to_dict()


def tool_error(
    action: str,
    code: str,
    message: str,
    data: dict | None = None,
):
    return ToolResult(
        ok=False,
        action=action,
        message=message,
        data=data or {},
        error={"code": code, "message": message},
    ).to_dict()


def tool_bool_result(
    action: str,
    success: bool,
    error_code: str = "OPERATION_FAILED",
    message: str = "",
    data: dict | None = None,
):
    result_data = {"success": success, **(data or {})}
    if success:
        return tool_success(action, data=result_data, message=message)
    return tool_error(
        action,
        error_code,
        message or "Operation failed.",
        data=result_data,
    )
