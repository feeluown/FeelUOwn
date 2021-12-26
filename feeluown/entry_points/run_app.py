import argparse
import asyncio
import logging
import os
import signal
import sys
import warnings

from feeluown.app import AppMode, create_app
from feeluown.utils.utils import is_port_inuse
from feeluown.cli import oncemain
from feeluown.fuoexec import fuoexec_load_rcfile, fuoexec_init
from feeluown.utils import aio
from feeluown.utils.dispatch import Signal  # noqa: E402

from .base import ensure_dirs, setup_config, setup_logger, create_config  # noqa: E402


logger = logging.getLogger(__name__)


def precheck(config) -> str:
    # Check if there will be any errors that cause start failure.
    # If there is an error, err_msg will not be empty.
    err_msg = ''

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

    return err_msg


def run_app(args: argparse.Namespace, adhoc=False):
    config = create_config()

    # Initialize config.
    #
    # Extract config items from args and setup config object,
    # since then, no more `args` object, only `config`.
    setup_config(args, config)

    # Load rcfile.
    #
    # In an ideal world, users are capable to do anything in rcfile,
    # including monkeypatch, so we should load rcfile as early as possible
    fuoexec_load_rcfile(config)

    # Precheck.
    #
    # When precheck failed, show error hint and exit.
    if adhoc is False:
        err_msg = precheck(config)
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

    # Prepare.
    #
    # Ensure requirements, raise SystemExit if failed.
    if adhoc is False:
        os.chdir(os.path.join(os.path.dirname(__file__), '../..'))
        ensure_dirs()
        setup_logger(config)
    else:
        # ignore all warnings since it will pollute the output
        warnings.filterwarnings("ignore")

    async def inner():
        Signal.setup_aio_support()
        app = create_app(config)

        # Do fuoexec initialization before app initialization.
        fuoexec_init(app)

        # Initialize app with config.
        #
        # all objects can do initialization here. some objects may emit signal,
        # some objects may connect with others signals.
        app.initialize()
        app.initialized.emit(app)

        if adhoc is False:
            app.load_state()

        # Handle signals.
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, app.exit)
        loop.add_signal_handler(signal.SIGINT, app.exit)

        if adhoc is False:
            sentinal: asyncio.Future = asyncio.Future()

            def shutdown(_):
                # Since about_to_shutdown signal may emit multiple times
                # (QApplication.aboutToQuit emits multiple times),
                # we should check if it is already done firstly.
                if not sentinal.done():
                    sentinal.set_result(0)

            app.about_to_shutdown.connect(shutdown, weak=False)

            if not app.has_gui and not app.has_server:
                logger.warning('running with no server and no window')
                return

            app.run()
            await sentinal
        else:
            await oncemain(app, args)

        Signal.teardown_aio_support()

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
    aio.run(inner())
