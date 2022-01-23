def options_to_str(options):
    """
    TODO: support complex value, such as list
    """
    return ",".join("{}={}".format(k, v)
                    for k, v in options.items())


class Request:
    """fuo 协议请求对象"""

    def __init__(self, cmd, cmd_args=None,
                 cmd_options=None, options=None,
                 has_heredoc=False, heredoc_word=None):
        self.cmd = cmd
        self.cmd_args = cmd_args or []
        self.cmd_options = cmd_options or {}

        self.options = options or {}

        self.has_heredoc = has_heredoc
        self.heredoc_word = heredoc_word

    def set_heredoc_body(self, body):
        assert self.has_heredoc is True and self.heredoc_word
        self.cmd_args = [body]

    @property
    def raw(self):
        """generate syntactically correct request"""

        def escape(value):
            # if value is not furi/float/integer, than we surround the value
            # with double quotes
            from feeluown.rpc.lexer import furi_re, integer_re, float_re

            regex_list = (furi_re, float_re, integer_re)
            for regex in regex_list:
                if regex.match(value):
                    break
            else:
                value = '"{}"'.format(value)
            return value

        # TODO: allow heredoc and args appear at the same time
        args_str = '' if self.has_heredoc else \
            ' '.join((escape(arg) for arg in self.cmd_args))
        options_str = options_to_str(self.cmd_options)
        if options_str:
            options_str = '[{}]'.format(options_str)
        raw = '{cmd} {args_str} {options_str} #: {req_options_str}'.format(
            cmd=self.cmd,
            args_str=args_str,
            options_str=options_str,
            req_options_str=options_to_str(self.options),
        )
        if self.has_heredoc:
            raw += ' <<{}\n{}\n{}\n\n'.format(self.heredoc_word,
                                              self.cmd_args[0],
                                              self.heredoc_word)
        return raw


class Response:
    def __init__(self, ok=True, text='', req=None, options=None):
        self.code = 'OK' if ok else 'Oops'
        self.text = text
        self.options = options or {}

        self.req = req
