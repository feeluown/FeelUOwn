import os

os.environ.setdefault('QT_API', 'pyqt6')
os.environ.setdefault('FEELUOWN_QT_API', 'pyqt6')

# pylint: disable=wrong-import-position
from feeluown.argparser import create_cli_parser  # noqa: E402


def _apply_startup_patches():
    """Apply runtime patches deferred from import time.

    Importing this module should stay cheap so that `--help`/`--version`
    and CLI fast paths do not pay for janus/mutagen/pydantic/Qt imports.
    """
    # Import locally to avoid pulling heavy deps at module import time.
    # pylint: disable=import-outside-toplevel
    from feeluown.utils.patch import (
        patch_janus,
        patch_mutagen,
        patch_pydantic,
    )
    patch_janus()
    patch_mutagen()
    patch_pydantic()

    try:
        from feeluown.utils.patch import patch_qeventloop
        patch_qeventloop()
    except ImportError:
        # qasync/qt is not installed
        # FIXME: should not catch the error at here
        pass


def run():
    """feeluown entry point.
    """

    args = create_cli_parser().parse_args()

    if args.cmd is not None:  # Only need to run some commands.
        if args.cmd == 'genicon':
            # genicon does not need runtime patches or daemon checks.
            # NOTE: janus/mutagen/pydantic/qeventloop patches are
            # intentionally skipped here: run_cli -> climain only forwards
            # via socket / generate_icon and never touches Signal aio queues
            # (Signal.setup_aio_support self-patches janus when needed).
            # pylint: disable=import-outside-toplevel
            from .run_cli import run_cli  # noqa: E402
            return run_cli(args)

        # If daemon is started, we send commands to daemon directly
        # we simple think the daemon is started as long as
        # the port 23333 is in use.
        # TODO: allow specify port in command line args.
        # NOTE: same as above, the daemon-client path needs no patches.
        # pylint: disable=import-outside-toplevel
        from feeluown.utils.utils import is_port_inuse  # noqa: E402
        if is_port_inuse(23333):
            from .run_cli import run_cli  # noqa: E402
            return run_cli(args)

    _apply_startup_patches()

    # pylint: disable=import-outside-toplevel
    from .run_app import run_app  # noqa: E402
    return run_app(args)
