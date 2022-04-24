from feeluown.server import Request
from .lexer import furi_re, integer_re, float_re


def options_to_str(options):
    """
    TODO: support complex value, such as list
    """
    return ",".join(f"{k}={v}"
                    for k, v in options.items())


def unparse(request: Request):
    """Generate source code for the request object"""

    def escape(value):
        # if value is not furi/float/integer, than we surround the value
        # with double quotes
        regex_list = (furi_re, float_re, integer_re)
        for regex in regex_list:
            if regex.match(value):
                break
        else:
            value = f'"{value}"'
        return value

    # TODO: allow heredoc and args appear at the same time
    args_str = '' if request.has_heredoc else \
        ' '.join((escape(arg) for arg in request.cmd_args))
    options_str = options_to_str(request.cmd_options)
    if options_str:
        options_str = f'[{options_str}]'
    raw = f'{request.cmd} {args_str} {options_str} #: {options_to_str(request.options)}'
    if request.has_heredoc:
        word = request.heredoc_word
        raw += f' <<{word}\n{request.cmd_args[0]}\n{word}\n\n'
    return raw
