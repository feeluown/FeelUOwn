from fuocore.utils import is_port_used
from .base import create_config, setup_argparse

from .run_cli import run_cli
from .run_app import run_once, run_forever


def run():
    """feeluown entry point"""

    args = setup_argparse().parse_args()
    config = create_config()

    # we are trying to run some commands
    if args.cmd is not None:

        # if daemon is started, we send commands to daemon directly
        # we simple think the daemon is started as long as
        # the port 23333 or 23334 is used
        if is_port_used(23333) or is_port_used(2334):
            return run_cli(args)

        # If daemon is not started, (some) commands can be meaningless,
        # such as `status`, `toggle`, `next`, etc. However, some other
        # commands can still be usefule. For instance, when people
        # want to fetch a song's playable url or see the lyric of a song,
        # they may run `fuo show fuo://xxx/songs/12345`. When people
        # want to make an audition of some music, they run
        # `fuo play fuo://xxx/songs/12345`. Under these circumstances,
        # we should try to make feeluown work as they expected to.
        # Currently, we have three such commands:
        cmds = ('show', 'play', 'search', 'download')
        if args.cmd in cmds:
            return run_once(args, config)

        raise SystemExit("can't connect to fuo daemon.")

    return run_forever(args, config)
