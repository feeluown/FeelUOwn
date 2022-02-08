class Cmd:
    """
    TODO: Maybe we should remove this class and use Request instead.
    """
    def __init__(self, action, *args, options=None):
        self.action = action
        self.args = args
        self.options = options or {}

    def __str__(self):
        return f'action:{self.action} args:{self.args}'
