import sys


# Choose proper qt-asyncio bridge(qumash/qasync/asyncqt) for
# different python version.
# https://github.com/feeluown/FeelUOwn/issues/346
if sys.version_info > (3, 5):
    try:
        from qasync import QEventLoop, QThreadExecutor
    except ImportError:
        raise RuntimeError("Please install python package 'qasync'")
else:
    # we use quamash instead of asyncqt since we have more experience in quamash
    try:
        from quamash import QEventLoop, QThreadExecutor
    except ImportError:
        raise RuntimeError("Please install python package 'quamash'.")


__all__ = (
    'QEventLoop',
    'QThreadExecutor',
)
