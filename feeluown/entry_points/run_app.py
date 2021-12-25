import asyncio
import sys
import logging
import asyncio
import sys
import os
import warnings
import signal

from feeluown.app import App
from feeluown.pubsub import HandlerV1 as PubsubHandlerV1
from feeluown.utils.utils import is_port_inuse
from feeluown.cli import oncemain
from feeluown.fuoexec import fuoexec_load_rcfile, fuoexec_init
from feeluown.utils import aio
from feeluown.utils.dispatch import Signal  # noqa: E402

from .base import ensure_dirs, setup_config, setup_logger, create_config  # noqa: E402


logger = logging.getLogger(__name__)


def precheck(config) -> str:
    need_server = config.mode & App.DaemonMode

    # Check if there will be any errors that cause start failure.
    # If there is an error, err_msg will not be empty.
    err_msg = ''

    # Check if ports are in use.
    if need_server:
        if is_port_inuse(config.RPC_PORT) or \
           is_port_inuse(config.PUBSUB_PORT):
            err_msg = (
                'App fails to start services because '
                f'either port {config.RPC_PORT} or {config.PUBSUB_PORT} '
                'was already in use. '
                'Please check if there was another FeelUOwn instance.'
            )

    return err_msg


def run_app(args, adhoc=False):
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
            if config.mode & App.GuiMode:
                from PyQt5.QtWidgets import QMessageBox, QApplication
                app = QApplication([])
                w = QMessageBox()
                w.setText(err_msg)
                w.finished.connect(lambda _: QApplication.quit())
                w.show()
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
        app = App.create(config)

        # do fuoexec initialization before app inits
        fuoexec_init(app)

        # initialize app with config
        #
        # all objects can do initialization here. some objects may emit signal,
        # some objects may connect with others signals.
        app.initialize()

        if adhoc is False:
            app.load_state()

        app.initialized.emit(app)
        if adhoc is True:
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
            #app.exit()
            pass

    signal.signal(signal.SIGTERM, handle_signal)

    try:
        if config.MODE & App.GuiMode:

            try:
                # HELP: QtWebEngineWidgets must be imported before a
                # QCoreApplication instance is created
                # TODO: add a command line option to control this import
                import PyQt5.QtWebEngineWidgets  # noqa
            except ImportError:
                logger.info('import QtWebEngineWidgets failed')

            from feeluown.utils.compat import DefaultQEventLoopPolicy
            asyncio.set_event_loop_policy(DefaultQEventLoopPolicy())
        aio.run(inner())
    except KeyboardInterrupt:
        print('ctrl-c')
        #app.exit()


async def forever_main(app):

    if not need_window and not need_server:
        logger.warning('running with no daemon and no window')
        return

    if need_server:
        platform = sys.platform.lower()
        if platform == 'darwin':
            try:
                from .global_hotkey_mac import MacGlobalHotkeyManager
            except ImportError as e:
                logger.warning("Can't start mac hotkey listener: %s", str(e))
            else:
                mac_global_hotkey_mgr = MacGlobalHotkeyManager()
                mac_global_hotkey_mgr.start()
        elif platform == 'linux':
            from feeluown.linux import run_mpris2_server
            run_mpris2_server(app)

        asyncio.create_task(app.server.run(
            app.get_listen_addr(),
            app.config.RPC_PORT
        ))
        asyncio.create_task(asyncio.start_server(
            PubsubHandlerV1(app.pubsub_gateway).handle,
            host=app.get_listen_addr(),
            port=app.config.PUBSUB_PORT,
        ))

    if need_window:
        from PyQt5.QtGui import QIcon, QPixmap, QGuiApplication

        future = asyncio.Future()

        def done_future():
            # Check if future is already done, because aboutToQuit signal
            # emits multiple times.
            if not future.done():
                future.set_result(0)

        QGuiApplication.setWindowIcon(QIcon(QPixmap('icons:feeluown.png')))
        # Set desktopFileName so that the window icon is properly shown under wayland.
        # I don't know if this setting brings other benefits or not.
        # https://github.com/pyfa-org/Pyfa/issues/1607#issuecomment-392099878
        QGuiApplication.setDesktopFileName('FeelUOwn')
        q_app  = QGuiApplication.instance()
        q_app.setQuitOnLastWindowClosed(not app.config.ENABLE_TRAY)
        q_app.setApplicationName('FeelUOwn')
        q_app.instance().aboutToQuit.connect(done_future)
        await future
