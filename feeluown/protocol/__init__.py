import logging

from .handlers import (
    HelpHandler,
    SearchHandler,
    PlayerHandler,
    PlaylistHandler,
    StatusHandler,
)

from .show import ShowHandler  # noqa
from .parser import CmdParser  # noqa


logger = logging.getLogger(__name__)


def exec_cmd(app, live_lyric, cmd):
    # FIXME: 要么只传 app，要么把 player, live_lyric 等分别传进来
    # 目前更使用 app 作为参数

    logger.debug('EXEC_CMD: ' + str(cmd))

    # 一些
    if cmd.action in ('help', ):
        handler = HelpHandler(app,
                              live_lyric=live_lyric)

    elif cmd.action in ('show', ):
        handler = ShowHandler(app,
                              live_lyric=live_lyric)

    elif cmd.action in ('search', ):
        handler = SearchHandler(app,
                                live_lyric=live_lyric)

    # 播放器相关操作
    elif cmd.action in (
        'play', 'pause', 'resume', 'stop', 'toggle',
    ):
        handler = PlayerHandler(app,
                                live_lyric=live_lyric)

    # 播放列表相关命令
    elif cmd.action in (
        'add', 'remove', 'clear', 'list',
        'next', 'previous',
    ):
        """
        add/remove fuo://local:song:xxx
        create xxx

        set playback_mode=random
        set volume=100
        """
        handler = PlaylistHandler(app,
                                  live_lyric=live_lyric)
    elif cmd.action in ('status',):
        handler = StatusHandler(app,
                                live_lyric=live_lyric)
    else:
        return 'Oops Command not found!\n'

    rv = 'ACK {}'.format(cmd.action)
    if cmd.args:
        rv += ' {}'.format(' '.join(cmd.args))
    try:
        cmd_rv = handler.handle(cmd)
        if cmd_rv:
            rv += '\n' + cmd_rv
    except Exception as e:
        logger.exception('handle cmd({}) error'.format(cmd))
        return '\nOops\n'
    else:
        rv = rv or ''
        return rv + '\nOK\n'
