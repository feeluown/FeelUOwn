from feeluown.utils.patch import patch_janus, patch_qeventloop
patch_janus()

try:
    patch_qeventloop()
except ImportError:
    # qasync/qt is not installed
    # FIXME: should not catch the error at here
    pass

# pylint: disable=wrong-import-position
from feeluown.utils.utils import is_port_inuse  # noqa: E402
from .base import setup_argparse  # noqa: E402
from .run_cli import run_cli  # noqa: E402
from .run_app import run_app  # noqa: E402


def run():
    """feeluown entry point.
    """

    args = setup_argparse().parse_args()

    if args.cmd is not None:  # Only need to run some commands.
        if args.cmd == 'genicon':
            return run_cli(args)

        # If daemon is started, we send commands to daemon directly
        # we simple think the daemon is started as long as
        # the port 23333 is in use.
        # TODO: allow specify port in command line args.
        if is_port_inuse(23333):
            return run_cli(args)

    return run_app(args)
