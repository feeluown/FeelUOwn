import os
import warnings

from feeluown.app import (
    create_app,
    init_app,
    run_app,
)
from feeluown.cli import oncemain
from feeluown.fuoexec import fuoexec_load_rcfile, fuoexec_init
from feeluown.utils import aio
from .base import (
    ensure_dirs,
    setup_config,
    setup_logger,
)


def run_forever(args, config):
    # ensure requiresments, raise SystemExit if failed
    os.chdir(os.path.join(os.path.dirname(__file__), '../..'))
    ensure_dirs()

    # In an ideal world, users are capable to do anything in rcfile,
    # including monkeypatch, so we should load rcfile as early as possible
    fuoexec_load_rcfile(config)

    # Extract config items from args and setup config object,
    # since then, no more `args` object, only `config`.
    setup_config(args, config)

    setup_logger(config)

    # create app instance with config
    #
    # nothing should happen except all objects are created
    app = create_app(config)

    # do fuoexec initialization before app inits
    fuoexec_init(app)

    # initialize app with config
    #
    # all objects can do initialization here. some objects may emit signal,
    # some objects may connect with others signals.
    init_app(app)

    app.initialized.emit(app)

    run_app(app)


def run_once(args, config):
    # ignore all warnings since it will pollute the output
    warnings.filterwarnings("ignore")
    fuoexec_load_rcfile(config)
    setup_config(args, config)

    async def inner():
        app = create_app(config)
        fuoexec_init(app)
        init_app(app)
        app.initialized.emit(app)
        try:
            await oncemain(app, args)
        except KeyboardInterrupt:
            print('keyboard event')
            app.player.stop()

    try:
        aio.run(inner())
    except KeyboardInterrupt:
        # TODO(cosven): call app.exit when app.exit is compatible with asyncio.run.
        pass
