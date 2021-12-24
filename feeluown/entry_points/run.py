from feeluown.utils.patch import patch_janus, patch_qeventloop
patch_janus()

try:
    patch_qeventloop()
except ImportError:
    # qasync/qt is not installed
    # FIXME: should not catch the error at here
    pass

# pylint: disable=wrong-import-position
import os
import warnings
import signal
from feeluown.app import create_app, init_app, forevermain
from feeluown.cli import oncemain
from feeluown.fuoexec import fuoexec_load_rcfile, fuoexec_init
from feeluown.utils import aio
from feeluown.utils.utils import is_port_inuse  # noqa: E402
from feeluown.utils.dispatch import Signal  # noqa: E402
from .base import ensure_dirs, setup_config, setup_logger  # noqa: E402
from .base import create_config, setup_argparse  # noqa: E402
from .run_cli import run_cli  # noqa: E402


def run():
    """feeluown entry point"""

    args = setup_argparse().parse_args()
    if args.cmd is not None:  # Only need to run some commands.
        if args.cmd == 'genicon':
            return run_cli(args)

        # If daemon is started, we send commands to daemon directly
        # we simple think the daemon is started as long as
        # the port 23333 is in use
        if is_port_inuse(2333):
            return run_cli(args)

        forever = False
        # If daemon is not started, (some) commands can be meaningless,
        # such as `status`, `toggle`, `next`, etc. However, some other
        # commands can still be usefule. For instance, when people
        # want to fetch a song's playable url or see the lyric of a song,
        # they may run `fuo show fuo://xxx/songs/12345`. When people
        # want to make an audition of some music, they run
        # `fuo play fuo://xxx/songs/12345`. Under these circumstances,
        # we should try to make feeluown work as they expected to.
        # Currently, we have three such commands:
        cmds = ('show', 'play', 'search')
        if args.cmd not in cmds:
            raise SystemExit("can't connect to fuo daemon.")
    else:
        forever = True

    config = create_config()

    if forever is True:
        # ensure requiresments, raise SystemExit if failed
        os.chdir(os.path.join(os.path.dirname(__file__), '../..'))
        ensure_dirs()
    else:
        # ignore all warnings since it will pollute the output
        warnings.filterwarnings("ignore")

    # In an ideal world, users are capable to do anything in rcfile,
    # including monkeypatch, so we should load rcfile as early as possible
    fuoexec_load_rcfile(config)

    # Extract config items from args and setup config object,
    # since then, no more `args` object, only `config`.
    setup_config(args, config)

    if forever is True:
        setup_logger(config)

    # create app instance with config
    #
    # nothing should happen except all objects are created
    app = create_app(config)

    async def run_app():
        Signal.setup_aio_support()

        # do fuoexec initialization before app inits
        fuoexec_init(app)

        # initialize app with config
        #
        # all objects can do initialization here. some objects may emit signal,
        # some objects may connect with others signals.
        init_app(app)

        if forever is True:
            app.load_state()

        app.initialized.emit(app)

        if forever is True:
            await forevermain(app)
        else:
            await oncemain(app, args)


    # App can exit in several ways
    #
    # GUI mode
    # 1. user clicks the tray icon exit button, which triggers QApplication.quit.
    # 2. SIGTERM is received.
    # 3. QApplication.quit is called. (For example, User press CMD-Q on macOS.)
    #
    # Daemon mode
    # 1. Ctrl-C
    # 2. SIGTERM
    def handle_signal(signum, _):
        if signum == signal.SIGTERM:
            app.exit()

    signal.signal(signal.SIGTERM, handle_signal)

    try:
        aio.run(run_app())
    except KeyboardInterrupt:
        if forever is True:
            app.exit()
