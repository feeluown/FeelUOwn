import asyncio
from functools import partial
import logging
import os
import time
from hashlib import md5

from .consts import CACHE_DIR


logger = logging.getLogger(__name__)


class ImgController(object):
    def __init__(self, app):
        super().__init__()

        self._app = app
        self.cache = _ImgCache(self._app)

    @asyncio.coroutine
    def get(self, img_url, img_name):
        fpath = self.cache.get(img_name)
        if fpath is not None:
            with open(fpath, 'rb') as f:
                content = f.read()
            self.cache.update(img_name)
            return content
        event_loop = asyncio.get_event_loop()
        future = event_loop.run_in_executor(
            None,
            partial(self._app.request.get, img_url))
        res = yield from future
        if res is None:
            return None
        fpath = self.cache.create(img_name)
        self.save(fpath, res.content)
        return res.content

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
