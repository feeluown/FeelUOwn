import asyncio
from functools import partial
import logging
import os
import time
from hashlib import md5

from feeluown.models import resolve
from feeluown.consts import CACHE_DIR


logger = logging.getLogger(__name__)


class ImgManager(object):
    """图片下载、缓存管理

    TOOD: 该模块相关逻辑需要重新梳理
    """
    def __init__(self, app):
        super().__init__()
        self._app = app
        self.cache = _ImgCache(self._app)

    def get_from_cache(self, img_name):
        fpath = self.cache.get(img_name)
        if fpath is not None:
            with open(fpath, 'rb') as f:
                content = f.read()
            return content
        return None

    async def get(self, img_url, img_name):
        if img_url.startswith('fuo://'):
            return resolve(img_url)
        fpath = self.cache.get(img_name)
        if fpath is not None:
            logger.info('read image:%s from cache', img_name)
            with open(fpath, 'rb') as f:
                content = f.read()
            self.cache.update(img_name)
            return content
        event_loop = asyncio.get_event_loop()
        action_msg = 'Downloading image from {}'.format(img_url)
        with self._app.create_action(action_msg) as action:
            res = await event_loop.run_in_executor(
                None,
                partial(self._app.request.get, img_url))
            if res is None:
                action.failed()
                return None
        fpath = self.cache.create(img_name)
        self.save(fpath, res.content)
        return res.content

    def get_from_files(self, img_url, img_name):
        logger.info('extract image from {}'.format(img_url))
        if img_url.endswith('mp3') or img_url.endswith('ogg') or img_url.endswith('wma'):
            from mutagen.mp3 import EasyMP3
            metadata = EasyMP3(img_url)
            content = metadata.tags._EasyID3__id3._DictProxy__dict['APIC:'].data
        elif img_url.endswith('m4a'):
            from mutagen.easymp4 import EasyMP4
            metadata = EasyMP4(img_url)
            content = metadata.tags._EasyMP4Tags__mp4._DictProxy__dict['covr'][0]
        return content

    def save(self, fpath, content):
        try:
            with open(fpath, 'wb') as f:
                f.write(content)
        except Exception:
            logger.exception('save image file failed')


class _ImgCache(object):
    '''Save img in cache dir.

    Each image is saved with a hash ``name``, which contain img last used
    timestamp.
    '''
    MAX_TOTAL_NUMBER = 100

    def __init__(self, app):
        super().__init__()

        self._app = app

    def _hash(self, img_name):
        pure_url = img_name.split('?')[0]
        return md5(pure_url.encode('utf-8')).hexdigest()

    def _gen_fname(self, hname):
        ts_str = str(int(time.time()))
        return hname + '-' + ts_str

    def create(self, img_name):
        '''return img file path'''
        hname = self._hash(img_name)
        fname = self._gen_fname(hname)
        logger.debug('create img cache for %s' % img_name)
        return self._get_path(fname)

    def update(self, img_name):
        hname = self._hash(img_name)
        new_fname = self._gen_fname(hname)
        new_fpath = self._get_path(new_fname)
        old_fpath = self.get(img_name)
        os.rename(old_fpath, new_fpath)
        logger.debug('update img cache for %s' % img_name)

    def get(self, img_name):
        hname = self._hash(img_name)
        for fname in os.listdir(CACHE_DIR):
            if fname.startswith(hname):
                logger.debug('get img cache for %s' % img_name)
                return self._get_path(fname)
        return None

    def delete(self, img_name):
        fpath = self.get(img_name)
        if fpath is not None:
            return os.remove(fpath)
        return False

    def _get_path(self, fname):
        return os.path.join(CACHE_DIR, fname)
