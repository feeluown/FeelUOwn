# -*- coding: utf-8 -*-
import os
import logging

from feeluown.utils import aio  # noqa
from .provider import provider  # noqa
from .provider_ui import LocalProviderUi

DEFAULT_MUSIC_FOLDER = os.path.expanduser('~') + '/Music'
DEFAULT_MUSIC_EXTS = ['mp3', 'ogg', 'wma', 'm4a', 'm4v', 'mp4', 'flac', 'ape', 'wav']

__alias__ = '本地音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '本地音乐'

logger = logging.getLogger(__name__)


def init_config(config):
    config.deffield('MUSIC_FOLDERS',
                    type_=list,
                    default=[DEFAULT_MUSIC_FOLDER],
                    desc='支持的音乐文件夹列表')
    config.deffield('MUSIC_FORMATS',
                    type_=list,
                    default=DEFAULT_MUSIC_EXTS,
                    desc='支持的音乐格式列表')
    config.deffield('CORE_LANGUAGE', type_=str, default='auto', desc='默认显示的语言')
    config.deffield('IDENTIFIER_DELIMITER',
                    type_=str,
                    default='',
                    desc='生成identifier时的连接符')
    config.deffield('EXPAND_ARTIST_SONGS',
                    type_=bool,
                    default=False,
                    desc='将专辑艺术家的专辑中歌曲加入到该艺术家的歌曲中')
    config.deffield('ARTIST_SPLITTER', type_=list, default=[',', '&'], desc='歌曲艺术家的分隔符')
    config.deffield('ARTIST_SPLITTER_IGNORANCE',
                    type_=list,
                    default=None,
                    desc='对艺术家信息使用分隔符时需要进行保护的字符串')
    config.deffield('SPLIT_ALBUM_ARTIST_NAME',
                    type_=bool,
                    default=False,
                    desc='支持使用分隔符分隔专辑艺术家')


async def autoload(app):
    await aio.run_fn(provider.scan, app.config.local, app.config.local.MUSIC_FOLDERS)

    app.show_msg('本地音乐扫描完毕')


def enable(app):
    logger.info('Register provider: %s', provider)
    app.library.register(provider)
    provider.initialize(app)

    app.started.connect(lambda *args: aio.create_task(autoload(*args)),
                        weak=False,
                        aioqueue=False)
    if app.mode & app.GuiMode:
        provider_ui = LocalProviderUi(app)
        app.pvd_ui_mgr.register(provider_ui)


def disable(app):
    logger.info('唔，不要禁用我')
