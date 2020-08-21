import asyncio
import logging
import os

from enum import Enum
from typing import List

from fuocore import aio
from fuocore.dispatch import Signal
from .consts import SONG_DIR

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    pending = 'pending'
    running = 'running'
    ok = 'ok'
    failed = 'failed'


class Downloader:
    async def run(self, url, filepath, **kwargs):
        pass

    def clean(self, filepath):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:  # noqa
                logger.exception(f'remove {filepath} failed, this should not happen')
            else:
                logger.info('download file faield, remove the tmp file')


class DownloadTask:
    def __init__(self, url, filename, downloader):
        self.url = url
        self.filename = filename

        self.downloader: Downloader = downloader
        #: task status
        self.status: DownloadStatus = DownloadStatus.pending


class CurlDownloader(Downloader):
    async def run(self, url, filepath, **kwargs):
        try:
            proc = await asyncio.create_subprocess_exec(
                'curl', url, '--output', filepath)
        except FileNotFoundError:
            logger.error("can't start download, curl is not installed")
            raise
        else:
            await proc.wait()
        return proc.returncode == 0


class DownloadManager:
    def __init__(self, app):
        """

        :type app: feeluown.app.App
        """
        self._tasks = []
        self._task_queue = asyncio.Queue()

        #: emit List[DownloadTask]
        self.tasks_changed = Signal()
        self.downloader: Downloader = CurlDownloader()

        self._path = SONG_DIR

    def initialize(self):
        aio.create_task(self.worker())

    def list_tasks(self) -> List[DownloadTask]:
        return self._tasks

    async def get(self, url, filename, headers=None, cookies=None):
        """download and save a file

        :param url: file url
        :param filename: target file name
        """
        # check if there exists same task
        for task in self.list_tasks():
            if task.filename == filename:
                logger.warning(f"task:{filename} has already been put into queue")
                return

        task = DownloadTask(url, filename, self.downloader)
        self._tasks.append(task)
        await self._task_queue.put(task)
        logger.info(f"task:{filename} has been put into queue")

    async def worker(self):
        while True:
            task = await self._task_queue.get()
            await self.run_task(task)

            # task done and remove task
            self._task_queue.task_done()
            self._tasks.remove(task)

            path = self._getpath(task.filename)
            logger.info(f'content has been saved into {path}')

    async def run_task(self, task):
        task.status = DownloadStatus.running
        filename = task.filename
        downloader = task.downloader

        filepath = self._getpath(filename)
        try:
            ok = await downloader.run(task.url, filepath)
        except asyncio.CancelledError:
            task.status = DownloadStatus.failed
        else:
            if ok:
                task.status = DownloadStatus.ok
            else:
                task.status = DownloadStatus.failed

        # clean up the temp file if needed
        if task.status is DownloadStatus.failed:
            downloader.clean(filepath)

    def is_file_downloaded(self, filename):
        return os.path.exists(self._getpath(filename))

    def _getpath(self, filename):
        return os.path.join(self._path, filename)
