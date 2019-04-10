class Request:
    """fuo 协议请求对象"""

    def __init__(self, cmd, cmd_args=None, cmd_options=None, options=None):
        self.cmd = cmd
        self.cmd_args = cmd_args or []
        self.cmd_options = cmd_options or {}

        self.options = options or {}
