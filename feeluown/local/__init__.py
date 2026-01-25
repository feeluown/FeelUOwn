# -*- coding: utf-8 -*-
import os
import logging

from feeluown.i18n import t
from feeluown.utils import aio  # noqa
from .provider import provider  # noqa

DEFAULT_MUSIC_FOLDER = os.path.expanduser("~") + "/Music"
DEFAULT_MUSIC_EXTS = ["mp3", "ogg", "wma", "m4a", "m4v", "mp4", "flac", "ape", "wav"]

__alias__ = "本地音乐"
__feeluown_version__ = "1.1.0"
__version__ = "0.1a0"
__desc__ = "本地音乐"

logger = logging.getLogger(__name__)


def init_config(config):
    config.deffield(
        "MUSIC_FOLDERS",
        type_=list,
        default=[DEFAULT_MUSIC_FOLDER],
        desc="Supported list of music folders",
    )
    config.deffield(
        "MUSIC_FORMATS",
        type_=list,
        default=DEFAULT_MUSIC_EXTS,
        desc="Supported list of music formats",
    )
    config.deffield(
        "CORE_LANGUAGE", type_=str, default="auto", desc="Default display language"
    )
    config.deffield(
        "IDENTIFIER_DELIMITER",
        type_=str,
        default="",
        desc="Delimiter used when generating identifiers",
    )
    config.deffield(
        "EXPAND_ARTIST_SONGS",
        type_=bool,
        default=False,
        desc="Include songs from album artists' albums in that artist's song list",
    )
    config.deffield(
        "ARTIST_SPLITTER",
        type_=list,
        default=[",", "&"],
        desc="Delimiters for song artists",
    )
    config.deffield(
        "ARTIST_SPLITTER_IGNORANCE",
        type_=list,
        default=None,
        desc="Strings to be protected when using delimiters on artist info",
    )
    config.deffield(
        "SPLIT_ALBUM_ARTIST_NAME",
        type_=bool,
        default=False,
        desc="Allow splitting album artist names using delimiters",
    )


async def autoload(app):
    await aio.run_fn(provider.scan, app.config.local, app.config.local.MUSIC_FOLDERS)

    app.show_msg(t("local-tracks-scan-finished"))


def enable(app):
    logger.info("Register provider: %s", provider)
    app.library.register(provider)
    provider.initialize(app)

    app.started.connect(
        lambda *args: aio.create_task(autoload(*args)), weak=False, aioqueue=False
    )
    if app.mode & app.GuiMode:
        from .provider_ui import LocalProviderUi

        provider_ui = LocalProviderUi(app)
        app.pvd_ui_mgr.register(provider_ui)


def disable(app):
    logger.info("Oops, local provider cannot be disabled")
