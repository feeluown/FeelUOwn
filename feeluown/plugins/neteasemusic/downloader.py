import asyncio
from functools import partial
import logging
import os

from PyQt5.QtCore import QObject, pyqtSignal

from feeluown.consts import SONG_DIR
from feeluown.utils import emit_requests_progress


logger = logging.getLogger(__name__)


class Downloader(QObject):
    download_progress_signal = pyqtSignal([int])

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.is_downloading = False
        self.current_song = None
        self.queue = []

    def _access_queue(self):
        if self.queue:
            song = self.queue.pop(0)
            self.download_song(song)
        else:
            self._app.message('下载队列下载完毕')

    def download_song(self, song):
        for s in self.queue:
            if s.mid == song.mid:
                self._app.message('%s 已经在下载队列中' % song.title)
                self._app.message('当前正在下载 %s' % self.current_song.title)
                return

        if self.is_downloading:
            if len(self.queue) > 10:
                self._app.message('下载队列已满，请稍后加入', error=True)
                return
            self.queue.append(song)
            self._app.message('%s 加入下载队列之中' % song.title)
            return

        self.is_downloading = True
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(self._download(song))

    @asyncio.coroutine
    def _download(self, song):
        f_name = song.filename
        f_path = os.path.join(SONG_DIR, f_name)
        if os.path.exists(f_path):
            logger.warning('%s have been downloaded' % song.title)
            self._app.message('%s 这首歌已经存在' % song.title)
            self.is_downloading = False
            self._access_queue()
            return True
        self.current_song = song
        if song.url is not None:
            try:
                event_loop = asyncio.get_event_loop()
                self._app.message('准备下载 %s' % song.title)
                res = song._api.http.get(song.url, stream=True, timeout=30)
                if res.status_code != 200:
                    raise Exception('response not ok while download song')
                future = event_loop.run_in_executor(
                    None,
                    partial(emit_requests_progress, res,
                            self.download_progress_signal))
                content = yield from future
                if not content:
                    raise Exception('error in downloaded song')
                with open(f_path, 'wb') as f:
                    f.write(content)
                logger.info('download song %s successfully' % song.title)
                self._app.message('%s 下载成功' % song.title)
                self.is_downloading = False
                self._access_queue()
                return True
            except Exception as e:
                logger.error(e)

        self._app.message('下载 %s 失败' % song.title, error=True)
        self.is_downloading = False
        self._access_queue()
        return False
