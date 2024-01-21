import asyncio
import logging
import os
import tempfile
import time
import uuid
from functools import partial
from hashlib import md5

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices, QImage

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
        if not img_url:
            return None
        if img_url.startswith('fuo://local'):
            # Before, `models.uri.resolve` is uesd to handle these non-std paths,
            # and it is not elegant in fact :(
            # HACK(cosven): please think about a better way in the future.
            provider = self._app.library.get('local')
            if provider is None:
                return None
            return provider.handle_with_path(img_url[11:])
        fpath = self.cache.get(img_name)
        if fpath is not None:
            logger.debug('read image:%s from cache', img_name)
            with open(fpath, 'rb') as f:
                content = f.read()
            self.cache.update(img_name)
            return content
        event_loop = asyncio.get_event_loop()
        try:
            # May return None.
            res = await event_loop.run_in_executor(
                None,
                partial(self._app.request.get, img_url))
        except:  # noqa
            res = None
            logger.error(f'Download image failed, url:{img_url}')
        if res is None:
            return
        fpath = self.cache.create(img_name)
        self.save(fpath, res.content)
        return res.content

    def get_from_files(self, img_url, img_name) -> bytes:
        logger.info('extract image from {}'.format(img_url))
        if img_url.endswith('mp3') or img_url.endswith('ogg') or img_url.endswith('wma'):
            from mutagen.mp3 import EasyMP3
            metadata_mp3 = EasyMP3(img_url)
            tags_mp3 = metadata_mp3.tags
            assert tags_mp3 is not None
            content = tags_mp3._EasyID3__id3._DictProxy__dict['APIC:'].data
        elif img_url.endswith('m4a'):
            from mutagen.easymp4 import EasyMP4
            metadata_mp4 = EasyMP4(img_url)
            tags_mp4 = metadata_mp4.tags
            assert tags_mp4 is not None
            content = tags_mp4._EasyMP4Tags__mp4._DictProxy__dict['covr'][0]
        else:
            raise Exception('Unsupported file type')
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


def open_image(img: QImage):
    tmpdir = tempfile.gettempdir()
    uid = str(uuid.uuid1())
    name = f'feeluown-img-{uid}.png'
    filepath = os.path.join(tmpdir, name)
    if img.save(filepath):
        QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
