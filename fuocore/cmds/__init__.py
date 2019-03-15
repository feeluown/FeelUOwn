import logging

from fuocore.excs import FuocoreException
from .base import cmd_handler_mapping

from .help import HelpHandler  # noqa
from .status import StatusHandler  # noqa
from .playlist import PlaylistHandler  # noqa
from .player import PlayerHandler  # noqa
from .search import SearchHandler  # noqa
from .show import ShowHandler  # noqa
from .exec_ import ExecHandler  # noqa

logger = logging.getLogger(__name__)


class CmdException(FuocoreException):
    pass


class Cmd:
    def __init__(self, action, *args, **kwargs):
        self.action = action
        self.args = args

    def __str__(self):
        return 'action:{} args:{}'.format(self.action, self.args)


class CmdLexer:
    r"""

    >>> list(CmdLexer().get_tokens('play fuo://local/songs/1'))
    ['play', 'fuo://local/songs/1']
    >>> list(CmdLexer().get_tokens("play <<EOF import os\nEOF\n"))
    ['play', 'import os']
    """
    def __init__(self, *args, **kwargs):
        pass

    def get_tokens(self, text):
        pos = 0
        while pos < len(text):
            c = text[pos]
            pos += 1
            if c == '<':  # similar as bash here document
                if text[pos] == '<':
                    pos += 1
                    token, pos = self.read_heredoc(text, pos)
                else:
                    token, pos = self.read_word(text, pos - 1)
            else:
                token, pos = self.read_word(text, pos - 1)
            if token is not None:
                yield token

    @classmethod
    def read_word(cls, text, pos):
        word = ''
        while pos < len(text):
            c = text[pos]
            pos += 1
            if c in (' ', '\t', '\n'):
                if word:
                    break
                continue
            else:
                word += c
        if not word:
            word = None
        return word, pos

    @classmethod
    def read_heredoc(cls, text, pos):
        delimiter, pos = cls.read_word(text, pos)
        if delimiter is None:
            raise CmdException('read heredoc failed: start delimiter not found')
        heredoc = ''
        while pos < len(text):
            c = text[pos]
            pos += 1
            if c == '\n':
                real_delimiter = delimiter + '\n'
                if text[pos:pos+len(real_delimiter)] == real_delimiter:
                    pos += len(real_delimiter)
                    break
                else:
                    heredoc += c
            else:
                heredoc += c
        else:
            raise CmdException('read heredoc failed: end delimiter not found.')
        if not heredoc:
            raise CmdException('read heredoc failed: heredoc has no content.')
        return heredoc, pos


class CmdParser:
    def parse(self, tokens_g):
        return Cmd(*tokens_g)


class CmdResolver:
    def __init__(self, cmd_handler_mapping):
        self.cmd_handler_mapping = cmd_handler_mapping

    def get_handler(self, cmd):
        return self.cmd_handler_mapping.get(cmd)


cmd_resolver = CmdResolver(cmd_handler_mapping)


def exec_cmd(cmd, *args, library, player, playlist, live_lyric):
    logger.debug('EXEC_CMD: ' + str(cmd))

    handler_cls = cmd_resolver.get_handler(cmd.action)
    if handler_cls is None:
        return '\nCommand not found! Oops\n'

    rv = 'ACK {}'.format(cmd.action)
    if cmd.args:
        args_text = ' {}'.format(' '.join(cmd.args))
        if len(args_text) > 60 or '\n' in args_text:
            rv += ' ...'
        else:
            rv += args_text
    try:
        handler = handler_cls(library=library,
                              player=player,
                              playlist=playlist,
                              live_lyric=live_lyric)
        cmd_rv = handler.handle(cmd)
        if cmd_rv:
            rv += '\n' + cmd_rv
    except Exception as e:
        logger.exception('handle cmd({}) error'.format(cmd))
        return '\nOops\n'
    else:
        rv = rv or ''
        return rv + '\nOK\n'


def interprete(text, *args, library, player, playlist, live_lyric):
    tokens = CmdLexer().get_tokens(text)
    cmd = CmdParser().parse(tokens)
    return exec_cmd(cmd,
                    library=library,
                    player=player,
                    playlist=playlist,
                    live_lyric=live_lyric)
