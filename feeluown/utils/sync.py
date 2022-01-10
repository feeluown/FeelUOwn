"""
Code are almost copied from asgiref.
https://github.com/django/asgiref/blob/6689c0a1e820a5c32532f069e945da8230d808ad/asgiref/sync.py
Lines that were changed are marked with `Note`.

Changes:

1. *2021-11-04*
   As only AsyncTosync is needed, other unrelated functions/classes are removed.
   It works well in known cases.
2. *2022-01-10*
   Since there can be only one QEventLoop instance, new_event_loop should
   create other event loop.
"""
import asyncio
import asyncio.coroutines
import functools
import inspect
import sys
import threading
import warnings
import queue
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from typing import Any


if sys.version_info >= (3, 7):
    import contextvars
    get_running_loop = asyncio.get_running_loop
else:
    contextvars = None
    get_running_loop = asyncio.get_event_loop


class _WorkItem:
    """
    Represents an item needing to be run in the executor.
    Copied from ThreadPoolExecutor, but it's private, so we're not
    going to rely on importing it.
    """

    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)


class CurrentThreadExecutor(Executor):
    """
    An Executor that actually runs code in the thread it is instantiated in.
    Passed to other threads running async code, so they can run sync code in
    the thread they came from.
    """

    def __init__(self):
        self._work_thread = threading.current_thread()
        self._work_queue = queue.Queue()
        self._broken = False

    def run_until_future(self, future):
        """
        Runs the code in the work queue until a result is available from the future.
        Should be run from the thread the executor is initialised in.
        """
        # Check we're in the right thread
        if threading.current_thread() != self._work_thread:
            raise RuntimeError(
                "You cannot run CurrentThreadExecutor from a different thread"
            )
        future.add_done_callback(self._work_queue.put)
        # Keep getting and running work items until we get the future we're waiting for
        # back via the future's done callback.
        try:
            while True:
                # Get a work item and run it
                work_item = self._work_queue.get()
                if work_item is future:
                    return
                work_item.run()
                del work_item
        finally:
            self._broken = True

    def submit(self, fn, *args, **kwargs):
        # Check they're not submitting from the same thread
        if threading.current_thread() == self._work_thread:
            raise RuntimeError(
                "You cannot submit onto CurrentThreadExecutor from its own thread"
            )
        # Check they're not too late or the executor errored
        if self._broken:
            raise RuntimeError("CurrentThreadExecutor already quit or is broken")
        # Add to work queue
        f = Future()
        work_item = _WorkItem(f, fn, args, kwargs)
        self._work_queue.put(work_item)
        # Return the future
        return f


def _restore_context(context):
    # Check for changes in contextvars, and set them to the current
    # context for downstream consumers
    for cvar in context:
        try:
            if cvar.get() != context.get(cvar):
                cvar.set(context.get(cvar))
        except LookupError:
            cvar.set(context.get(cvar))


def _iscoroutinefunction_or_partial(func: Any) -> bool:
    # Python < 3.8 does not correctly determine partially wrapped
    # coroutine functions are coroutine functions, hence the need for
    # this to exist. Code taken from CPython.
    if sys.version_info >= (3, 8):
        return asyncio.iscoroutinefunction(func)
    else:
        while inspect.ismethod(func):
            func = func.__func__
        while isinstance(func, functools.partial):
            func = func.func

        return asyncio.iscoroutinefunction(func)


class AsyncToSync:
    """
    Utility class which turns an awaitable that only works on the thread with
    the event loop into a synchronous callable that works in a subthread.
    If the call stack contains an async loop, the code runs there.
    Otherwise, the code runs in a new loop in a new thread.
    Either way, this thread then pauses and waits to run any thread_sensitive
    code called from further down the call stack using SyncToAsync, before
    finally exiting once the async task returns.
    """

    # Maps launched Tasks to the threads that launched them (for locals impl)
    # launch_map: "Dict[asyncio.Task[object], threading.Thread]" = {}
    # Note(cosven): we do not need launch_map since we do not use locals impl.

    # Keeps track of which CurrentThreadExecutor to use. This uses an asgiref
    # Local, not a threadlocal, so that tasks can work out what their parent used.
    #
    # Note(cosven): we can use threading.Local because we only use AsyncToSync
    # and never use SyncToAsync.
    executors = threading.local()

    def __init__(self, awaitable, force_new_loop=False):
        if not callable(awaitable) or not _iscoroutinefunction_or_partial(awaitable):
            # Python does not have very reliable detection of async functions
            # (lots of false negatives) so this is just a warning.
            warnings.warn(
                "async_to_sync was passed a non-async-marked callable", stacklevel=2
            )
        self.awaitable = awaitable
        try:
            self.__self__ = self.awaitable.__self__
        except AttributeError:
            pass
        if force_new_loop:
            # They have asked that we always run in a new sub-loop.
            self.main_event_loop = None
        else:
            try:
                self.main_event_loop = get_running_loop()
            except RuntimeError:
                # Note(cosven): we never use SyncToAsync
                #
                # There's no event loop in this thread. Look for the threadlocal if
                # we're inside SyncToAsync
                # main_event_loop_pid = getattr(
                #     SyncToAsync.threadlocal, "main_event_loop_pid", None
                # )
                # We make sure the parent loop is from the same process - if
                # they've forked, this is not going to be valid any more (#194)
                # if main_event_loop_pid and main_event_loop_pid == os.getpid():
                #     self.main_event_loop = getattr(
                #         SyncToAsync.threadlocal, "main_event_loop", None
                #     )
                # else:
                self.main_event_loop = None

    def __call__(self, *args, **kwargs):
        # You can't call AsyncToSync from a thread with a running event loop
        try:
            event_loop = get_running_loop()
        except RuntimeError:
            pass
        else:
            if event_loop.is_running():
                raise RuntimeError(
                    "You cannot use AsyncToSync in the same thread as "
                    "an async event loop - "
                    "just await the async function directly."
                )

        if contextvars is not None:
            # Wrapping context in list so it can be reassigned from within
            # `main_wrap`.
            context = [contextvars.copy_context()]
        else:
            context = None

        # Make a future for the return information
        call_result = Future()
        # Get the source thread
        source_thread = threading.current_thread()
        # Make a CurrentThreadExecutor we'll use to idle in this thread - we
        # need one for every sync frame, even if there's one above us in the
        # same thread.
        if hasattr(self.executors, "current"):
            old_current_executor = self.executors.current
        else:
            old_current_executor = None
        current_executor = CurrentThreadExecutor()
        self.executors.current = current_executor
        # Use call_soon_threadsafe to schedule a synchronous callback on the
        # main event loop's thread if it's there, otherwise make a new loop
        # in this thread.
        try:
            awaitable = self.main_wrap(
                args, kwargs, call_result, source_thread, sys.exc_info(), context
            )

            if not (self.main_event_loop and self.main_event_loop.is_running()):
                # Make our own event loop - in a new thread - and run inside that.

                # Note(cosven): There must be only one QEventLoop instance,
                # so we should use asyncio.DefaultEventLoopPolicy to create new
                # event loops.
                policy = asyncio.get_event_loop_policy()
                try:
                    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
                    loop = asyncio.new_event_loop()
                finally:
                    asyncio.set_event_loop_policy(policy)

                loop_executor = ThreadPoolExecutor(max_workers=1)
                loop_future = loop_executor.submit(
                    self._run_event_loop, loop, awaitable
                )
                if current_executor:
                    # Run the CurrentThreadExecutor until the future is done
                    current_executor.run_until_future(loop_future)
                # Wait for future and/or allow for exception propagation
                loop_future.result()
            else:
                # Call it inside the existing loop
                self.main_event_loop.call_soon_threadsafe(
                    self.main_event_loop.create_task, awaitable
                )
                if current_executor:
                    # Run the CurrentThreadExecutor until the future is done
                    current_executor.run_until_future(call_result)
        finally:
            # Clean up any executor we were running
            if hasattr(self.executors, "current"):
                del self.executors.current
            if old_current_executor:
                self.executors.current = old_current_executor
            if contextvars is not None:
                _restore_context(context[0])

        # Wait for results from the future.
        return call_result.result()

    def _run_event_loop(self, loop, coro):
        """
        Runs the given event loop (designed to be called in a thread).
        """
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            try:
                # mimic asyncio.run() behavior
                # cancel unexhausted async generators
                if sys.version_info >= (3, 7, 0):
                    tasks = asyncio.all_tasks(loop)
                else:
                    tasks = asyncio.Task.all_tasks(loop)
                for task in tasks:
                    task.cancel()

                async def gather():
                    await asyncio.gather(*tasks, return_exceptions=True)

                loop.run_until_complete(gather())
                for task in tasks:
                    if task.cancelled():
                        continue
                    if task.exception() is not None:
                        loop.call_exception_handler(
                            {
                                "message": "unhandled exception during loop shutdown",
                                "exception": task.exception(),
                                "task": task,
                            }
                        )
                if hasattr(loop, "shutdown_asyncgens"):
                    loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
                asyncio.set_event_loop(self.main_event_loop)

    def __get__(self, parent, objtype):
        """
        Include self for methods
        """
        func = functools.partial(self.__call__, parent)
        return functools.update_wrapper(func, self.awaitable)

    async def main_wrap(
        self, args, kwargs, call_result, source_thread, exc_info, context
    ):
        """
        Wraps the awaitable with something that puts the result into the
        result/exception future.
        """
        if context is not None:
            _restore_context(context[0])

        # current_task = SyncToAsync.get_current_task()
        # self.launch_map[current_task] = source_thread
        try:
            # If we have an exception, run the function inside the except block
            # after raising it so exc_info is correctly populated.
            if exc_info[1]:
                try:
                    raise exc_info[1]
                except BaseException:
                    result = await self.awaitable(*args, **kwargs)
            else:
                result = await self.awaitable(*args, **kwargs)
        except BaseException as e:
            call_result.set_exception(e)
        else:
            call_result.set_result(result)
        finally:
            # del self.launch_map[current_task]

            if context is not None:
                context[0] = contextvars.copy_context()
