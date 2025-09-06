import asyncio
import sys

from qasync import QEventLoop, QThreadExecutor
from PyQt5.QtWidgets import QApplication

try:
    from qasync import DefaultQEventLoopPolicy
except ImportError:
    # From qasync>=0.28, the class DefaultQEventLoopPolicy is removed
    # when python version >= 3.12
    class DefaultQEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
        def new_event_loop(self):
            return QEventLoop(QApplication.instance() or QApplication(sys.argv))


__all__ = (
    'QEventLoop',
    'QThreadExecutor',
    'DefaultQEventLoopPolicy'
)
