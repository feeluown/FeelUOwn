from .cmd import Cmd
from .excs import HandlerException
from .base import AbstractHandler


class HelpHandler(AbstractHandler):
    cmds = 'help'

    def handle(self, cmd: Cmd):
        return self.handle_help(*cmd.args)

    def handle_help(self, cmdname: str):
        # pylint: disable=import-outside-toplevel
        from feeluown.server.dslv2 import create_dsl_parser, get_subparser  # noqa

        parser = create_dsl_parser()
        subparser = get_subparser(parser, cmdname)
        if subparser is None:
            raise HandlerException(f'help: no such cmd: {cmdname}')
        return subparser.format_help()
