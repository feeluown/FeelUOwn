import asyncio

from qasync import QEventLoop, QThreadExecutor, AllEvents
from PyQt6.QtWidgets import QApplication


# Work around Python 3.14 running-loop checks triggered by qasync shutdown.
class PatchedQEventLoop(QEventLoop):
    def run_until_complete(self, future):
        if self.is_running():
            raise RuntimeError("Event loop already running")

        future = asyncio.ensure_future(future, loop=self)

        def stop(*args):
            self.stop()

        future.add_done_callback(stop)
        try:
            self.run_forever()
        finally:
            future.remove_done_callback(stop)

        prev_loop = asyncio.events._get_running_loop()
        asyncio.events._set_running_loop(self)
        try:
            QApplication.instance().eventDispatcher().processEvents(AllEvents)
        finally:
            asyncio.events._set_running_loop(prev_loop)

        if not future.done():
            raise RuntimeError("Event loop stopped before Future completed.")

        return future.result()


__all__ = (
    'QEventLoop',
    'QThreadExecutor',
)
