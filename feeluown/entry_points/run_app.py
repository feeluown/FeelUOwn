import argparse
import asyncio
import logging
import signal
import sys
import warnings

from feeluown.app import AppMode, create_app, create_config
from feeluown.utils.utils import is_port_inuse
from feeluown.fuoexec import fuoexec_load_rcfile, fuoexec_init
from feeluown.utils import aio
from feeluown.utils.dispatch import Signal  # noqa: E402

from .base import ensure_dirs, setup_config, setup_logger  # noqa: E402


logger = logging.getLogger(__name__)


def run_app(args: argparse.Namespace):
    args, config = before_start_app(args)
    aio.run(start_app(args, config))


def before_start_app(args):
    """
    Prepare things that app depends on and initialize things which don't depend on app.
    """
    config = create_config()

    # Load rcfile.
    #
    # In an ideal world, users are capable to do anything in rcfile,
    # including monkeypatch, so we should load rcfile as early as possible
    fuoexec_load_rcfile(config)

    # Initialize config.
    #
    # Extract config items from args and setup config object.
    # Arg has higher priority than config. If a parameter was set both in
    # args and config, the arg can override the value.
    setup_config(args, config)

    # Precheck.
    #
    # When precheck failed, show error hint and exit.
    precheck(args, config)

    # Prepare.
    #
    # Ensure requirements, raise SystemExit if failed.
    ensure_dirs()
    setup_logger(config)
    # Ignore all warnings since it will pollute the output.
    if AppMode.cli in AppMode(config.MODE):
        warnings.filterwarnings("ignore")

    # Run.
    #
    if AppMode.gui in AppMode(config.MODE):
        try:
            # HELP: QtWebEngineWidgets must be imported before a
            #   QCoreApplication instance is created.
            # TODO: add a command line option to control this import.
            import PyQt5.QtWebEngineWidgets  # type: ignore # noqa
        except ImportError:
            logger.info('import QtWebEngineWidgets failed')
        from feeluown.utils.compat import DefaultQEventLoopPolicy
        asyncio.set_event_loop_policy(DefaultQEventLoopPolicy())
    return args, config


async def start_app(args, config, sentinal=None):
    """
    The param sentinal is currently only used for unittest.
    """
    Signal.setup_aio_support()

    app = create_app(args, config)

    # Do fuoexec initialization before app initialization.
    fuoexec_init(app)

    # Initialize app with config.
    #
    # all objects can do initialization here. some objects may emit signal,
    # some objects may connect with others signals.
    app.initialize()
    app.initialized.emit(app)

    # Load last state.
    app.load_state()

    def sighanlder(signum, _):
        logger.info('Signal %d is received', signum)
        app.exit()

    # Handle signals.
    signal.signal(signal.SIGTERM, sighanlder)
    signal.signal(signal.SIGINT, sighanlder)

    if sentinal is None:
        sentinal: asyncio.Future = asyncio.Future()

    def shutdown(_):
        # Since about_to_shutdown signal may emit multiple times
        # (QApplication.aboutToQuit emits multiple times),
        # we should check if it is already done firstly.
        if not sentinal.done():
            sentinal.set_result(0)

    app.about_to_shutdown.connect(shutdown, weak=False)

    # App can exit in several ways.
    #
    # GUI mode:
    # 1. QApplication.quit. QApplication.quit can be called under several circumstances
    #    1. User press CMD-Q on macOS.
    #    2. User clicks the tray icon exit button.
    # 2. SIGTERM is received.
    #
    # Daemon mode:
    # 1. Ctrl-C
    # 2. SIGTERM
    app.run()
    await sentinal

    Signal.teardown_aio_support()


def precheck(args, config):
    # Check if there will be any errors that cause start failure.
    # If there is an error, err_msg will not be empty.
    err_msg = ''

    if AppMode.cli in AppMode(config.MODE):
        # If daemon is not started, some commands can be meaningless,
        # such as `status`, `toggle`, `next`, etc. However, some other
        # commands can still be usefule. For instance, when people
        # want to fetch a song's playable url or see the lyric of a song,
        # they may run `fuo show fuo://xxx/songs/12345`. When people
        # want to make an audition of some music, they run
        # `fuo play fuo://xxx/songs/12345`. Under these circumstances,
        # we should try to make feeluown work as they expected to.
        if args.cmd not in ('show', 'play', 'search'):
            err_msg = f"Run {args.cmd} failed, can't connect to fuo server."

    # Check if ports are in use.
    if AppMode.server in AppMode(config.MODE):
        if is_port_inuse(config.RPC_PORT) or \
           is_port_inuse(config.PUBSUB_PORT):
            err_msg = (
                'App fails to start services because '
                f'either port {config.RPC_PORT} or {config.PUBSUB_PORT} '
                'was already in use. '
                'Please check if there was another FeelUOwn instance.'
            )

    if err_msg:
        if AppMode.gui in AppMode(config.MODE):
            from PyQt5.QtWidgets import QMessageBox, QApplication
            qapp = QApplication([])
            w = QMessageBox()
            w.setText(err_msg)
            # The type annotation for `finished` is wrong.
            w.finished.connect(lambda _: QApplication.quit())  # type: ignore
            w.show()
            qapp.exec()
        else:
            print(err_msg)
        sys.exit(1)
