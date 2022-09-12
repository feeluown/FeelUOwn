# -*- coding: utf-8 -*-
import logging
from functools import partial

from feeluown.utils import aio

from .patch import patch_mutagen
patch_mutagen()

from .consts import DEFAULT_MUSIC_FOLDER, DEFAULT_MUSIC_EXTS
from .provider import provider


__alias__ = '本地音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '本地音乐'

logger = logging.getLogger(__name__)


def init_config(config):
    config.deffield('MUSIC_FOLDERS', type_=list, default=[DEFAULT_MUSIC_FOLDER], desc='')
    config.deffield('MUSIC_FORMATS', type_=list, default=DEFAULT_MUSIC_EXTS, desc='')
    config.deffield('CORE_LANGUAGE', type_=str, default='auto', desc='')
    config.deffield('IDENTIFIER_DELIMITER', type_=str, default='', desc='')
    config.deffield('EXPAND_ARTIST_SONGS', type_=bool, default=False, desc='')


async def autoload(app):
    await aio.run_fn(provider.scan,
                     app.config.local,
                     app.config.local.MUSIC_FOLDERS)

    app.show_msg('本地音乐扫描完毕')
    if app.mode & app.GuiMode:
        app.coll_uimgr.refresh()


def show_provider(req):
    from .ui import LibraryRenderer
    if hasattr(req, 'ctx'):
        app = req.ctx['app']
    else:
        app = req  # 兼容老版本
    app.pl_uimgr.clear()
    # app.playlists.add(provider.playlists)

    app.ui.left_panel.my_music_con.hide()
    app.ui.left_panel.playlists_con.hide()

    aio.run_afn(
        app.ui.table_container.set_renderer,
        LibraryRenderer(provider.songs, provider.albums, provider.artists))


def enable(app):
    logger.info('Register provider: %s', provider)
    app.library.register(provider)
    provider.initialize(app)

    app.initialized.connect(lambda *args: aio.create_task(autoload(*args)),
                            weak=False, aioqueue=False)
    if app.mode & app.GuiMode:
        app.browser.route('/local')(show_provider)
        pm = app.pvd_uimgr.create_item(
            name=provider.identifier,
            text='本地音乐',
            symbol='♪ ',
            desc='点击显示所有本地音乐',
        )
        pm.clicked.connect(partial(app.browser.goto, uri='/local'), weak=False)
        app.pvd_uimgr.add_item(pm)


def disable(app):
    logger.info('唔，不要禁用我')
