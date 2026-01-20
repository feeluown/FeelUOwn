# flake8: noqa

import asyncio
import sys


def patch_qeventloop():
    # patch note::
    #
    # asyncio.wrap_future should set loop to self, otherwise, we can not call run_in_executor
    # in another thread(the loop not belongs to). The event loop implemented in asyncio
    # library also does this.

    from .compat import QEventLoop, QThreadExecutor

    def run_in_executor(self, executor, callback, *args):
        """Run callback in executor.

        If no executor is provided, the default executor will be used, which defers execution to
        a background thread.
        """
        # pylint: disable=all

        self._logger.debug('Running callback {} with args {} in executor'.format(callback, args))
        if isinstance(callback, asyncio.Handle):
            assert not args
            assert not isinstance(callback, asyncio.TimerHandle)
            if callback._cancelled:
                f = asyncio.Future()
                f.set_result(None)
                return f
            callback, args = callback.callback, callback.args

        if executor is None:
            self._logger.debug('Using default executor')
            executor = self.get_default_executor()

        if executor is None:
            self._logger.debug('Creating default executor')
            self.set_default_executor_v2(QThreadExecutor())
            executor = self.get_default_executor()

        return asyncio.wrap_future(executor.submit(callback, *args), loop=self)

    def get_default_executor(self):
        return getattr(self, 'default_executor', None)

    def set_default_executor_v2(self, executor):
        setattr(self, 'default_executor', executor)

        # QEventLoop will shutdown executor when loop is closed
        self.set_default_executor(executor)

    QEventLoop.get_default_executor = get_default_executor
    QEventLoop.set_default_executor_v2 = set_default_executor_v2
    QEventLoop.run_in_executor = run_in_executor


def patch_janus():
    """
    https://github.com/aio-libs/janus/issues/250
    """

    import janus

    janus.current_loop = asyncio.get_event_loop


def patch_mutagen():

    from mutagen.id3 import _specs

    old_decode_terminated = _specs.decode_terminated

    def decode_terminated(data, encoding, strict=True):
        """
        Some songs in China have their ID3 information encoded in GBK,
        but their metadata indicates latin1 encoding, so mutagen parsing
        returns incorrect results.

        Here, we did not choose to reimplement the original function,
        but process its return value, which better ensures our implementation
        does not affect other mutagen logic.

        However, this approach has an issue: the original function has already
        performed decode and encode, and we repeat encode and decode here,
        theoretically causing some performance overhead.

        We welcome interested peers to optimize.



        > **NOTE**: According to the ID3 2.3/2.4 specification, GBK encoding is *apparently*
        > illegal in the first place; the spec states only these four are supported:
        > latin1, utf16, utf_16_be, utf8.
        > Mutagen indeed implements according to the spec, but reality is always cruel.
        """
        orig_value, data = old_decode_terminated(data, encoding, strict)
        value = orig_value
        if encoding == 'latin1':
            value = orig_value.encode('latin1')
            # Refer to the deepin-music-player project’s easymp3.py for implementation
            for codec in ['gbk', 'big5', 'utf-8', 'iso-8559-15', 'cp1251']:
                try:
                    value = value.decode(codec)
                except (UnicodeDecodeError, LookupError):
                    # decode failed or codec not found
                    pass
                else:
                    break
            else:
                value = orig_value
        return value, data

    _specs.decode_terminated = decode_terminated


def patch_pydantic():
    """
    For some reason, some plugins already use pydantic v2 and they only use
    pydantic.v1 package. Make them compat with pydantic v1 in an hacker way :)
    """
    try:
        import pydantic.v1
    except ImportError:
        import pydantic
        sys.modules['pydantic.v1'] = pydantic
