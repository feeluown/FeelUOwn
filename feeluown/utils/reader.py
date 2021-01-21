"""
Provider often splits resource which has large body to chunks, such as
a large playlist with 10k songs, the client need to send several request
to fetch the whole playlist. Generally, we call this design Pagination.
Moreover, different provider has different pagination API.
For feeluown, we want a unified API, so we create the Reader class.
"""
import logging
from collections.abc import Iterable, Sequence, AsyncIterable

from feeluown.excs import ReadFailed, ProviderIOError

logger = logging.getLogger(__name__)

__all__ = (
    'SequentialReader',
    'RandomReader',
    'RandomSequentialReader',
    'wrap',
)


class Reader:
    """Reader base class"""

    allow_sequential_read = False
    allow_random_read = False
    is_async = False

    def __init__(self):
        self._objects = []


class SequentialReadMixin:

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.read_next()
        except StopIteration:
            raise
        # TODO: caller should not crash when reader raise other exception
        except Exception as e:
            raise ProviderIOError('read next obj failed') from e


class AsyncSequntialReadMixin:
    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.a_read_next()
        except StopAsyncIteration:
            raise
        # TODO: caller should not crash when reader raise other exception
        except Exception as e:
            raise ProviderIOError('read next obj failed') from e


class BaseSequentialReader(Reader):
    allow_sequential_read = True

    def __init__(self, g, count, offset=0):
        """init

        :param g: Python generator
        :param offset: current offset
        :param count: total count. count can be None, which means the
                      total count is unknown. When it is unknown, be
                      CAREFUL to use list(reader).
        """
        super().__init__()
        self._g = g
        self.count = count
        self.offset = offset


class SequentialReader(BaseSequentialReader, SequentialReadMixin):
    """Help you sequential read data

    We only want to launch web request when we need the resource
    Formerly, we use Python generator to achieve this lazy read
    feature. However, we can't extract any read meta info,
    such as total count and current offset, from the ordinary
    generator.

    SequentialReader implements the iterator protocol, wraps the
    generator and store the reader state.

    .. note::

         iterating may be a blocking operation.

    **Usage example**:

    >>> def fetch_songs(page=1, page_size=50):
    ...     return list(range(page * page_size,
    ...                       (page + 1) * page_size))
    ...
    >>> def create_songs_g():
    ...     page = 0
    ...     total_page = 2
    ...     page_size = 2
    ...
    ...     def g():
    ...         nonlocal page, page_size
    ...         while page < total_page:
    ...            for song in fetch_songs(page, page_size):
    ...                yield song
    ...            page += 1
    ...
    ...     total = total_page * page_size
    ...     return SequentialReader(g(), total)
    ...
    >>> g = create_songs_g()
    >>> g.offset, g.count
    (0, 4)
    >>> next(g), next(g)
    (0, 1)
    >>> list(g)
    [2, 3]
    >>> g.offset, g.count
    (4, 4)

    .. versionadded:: 3.1
    """

    def readall(self):
        if self.count is None:
            raise ReadFailed("can't readall when count is unknown")
        list(self)
        return self._objects

    def read_next(self):
        if self.count is None or self.offset < self.count:
            try:
                obj = next(self._g)
            except StopIteration:
                if self.count is None:
                    self.count = self.offset + 1
                raise
        else:
            raise StopIteration
        self.offset += 1
        self._objects.append(obj)
        return obj


class RandomReader(Reader):
    allow_random_read = True

    def __init__(self, count, read_func, max_per_read):
        """random reader constructor

        :param int count: total number of objects
        :param function read_func: func(start: int, end: int) -> list
        :param int max_per_read: max count per read, it must big than 0
        """
        super().__init__()
        self.count = count
        self._ranges = []  # list of tuple
        self._objects = [None] * count
        self._read_func = read_func

        assert max_per_read > 0, 'max_per_read must big than 0'
        self._max_per_read = max_per_read

    def read(self, index):
        """read object by index

        if the object is not already read, this method may trigger IO operation.

        :raises ReadFailed: when the IO operation fails
        """
        yes, r = self._has_index(index)
        if yes:
            return self._objects[index]
        self._read_range(*r)
        return self._objects[index]

    def readall(self):
        """read all objects

        :return list: list of objects
        :raises ReadFailed:
        """
        # all objects have been read
        if len(self._ranges) == 1 and self._ranges[0] == (0, self.count):
            return self._objects

        start = 0
        end = 0
        count = self.count
        while end < count:
            end = min(count, end + self._max_per_read)
            self._read_range(start, end)
            start = end
        return self._objects

    # def explain_readall(self):
    #     read_times = self.count / self._max_per_read
    #     if self.count % self._max_per_read > 0:
    #         read_times += 1
    #     return {'count': self.count,
    #             'max_per_read': self._max_per_read,
    #             'read_times': read_times}

    def _read_range(self, start, end):
        # TODO: make this method thread safe
        assert start <= end, "start should less than end"
        try:
            logger.info('trigger read_func(%d, %d)', start, end)
            objs = self._read_func(start, end)
        except:  # noqa: E722
            raise ReadFailed('read_func raise error')
        else:
            expected = end - start
            actual = len(objs)
            if expected != actual:
                raise ReadFailed('read_func returns unexpected number of objects: '
                                 'expected={}, actual={}'
                                 .format(expected, actual))
            self._objects[start:end] = objs
            self._refresh_ranges()

    def _has_index(self, index):
        has_been_read = False
        left_index = right_index = None  # [left, right) -> range to read

        gt_index = None
        for r in self._ranges:
            start, end = r
            if index < start:
                # [, gt_index) index [start, end)
                gt_index = gt_index if gt_index is not None else 0
                left_index = index
                right_index = min(start, index + self._max_per_read)
                # trick: read as much as possible at a time to improve performance
                if start - gt_index <= self._max_per_read:
                    left_index = gt_index
                    right_index = start
                break
            # found index
            elif start <= index < end:
                has_been_read = True
                left_index, right_index = start, end
                break
            else:
                gt_index = end
        else:
            # default read range [index, min(index + max_per_read, self.count))
            left_index = index
            right_index = min(index + self._max_per_read, self.count)
            # trick: read as much as possible at a time to improve performance
            if gt_index is not None:
                if self.count - gt_index < self._max_per_read:
                    left_index = gt_index
                    right_index = self.count
        return has_been_read, (left_index, right_index)

    def _refresh_ranges(self):
        ranges = []
        start = None
        for i, obj in enumerate(self._objects):
            if start is None and obj is not None:
                start = i
                continue
            if start is not None and obj is None:
                ranges.append((start, i))
                start = None
        if start is not None:
            ranges.append((start, len(self._objects)))
        self._ranges = ranges


class RandomSequentialReader(RandomReader, SequentialReadMixin):
    """random reader which support sequential read"""

    allow_sequential_read = True

    def __init__(self, count, read_func, max_per_read=100):
        super().__init__(count, read_func, max_per_read=max_per_read)

        self.offset = 0

    def read_next(self):
        if self.offset >= self.count:
            raise StopIteration
        obj = self.read(self.offset)
        self.offset += 1
        return obj


class AsyncSequentialReader(BaseSequentialReader, AsyncSequntialReadMixin):
    is_async = True

    async def a_readall(self):
        if self.count is None:
            raise ReadFailed("can't readall when count is unknown")
        async for _ in self:
            pass
        return self._objects

    async def a_read_next(self):
        if self.count is None or self.offset < self.count:
            try:
                obj = await self._g.asend(None)
            except StopAsyncIteration:
                if self.count is None:
                    self.count = self.offset + 1
                raise
        else:
            raise StopAsyncIteration
        self.offset += 1
        self._objects.append(obj)
        return obj


def wrap(iterable):
    """create a reader from an iterable

    >>> reader = wrap([1, 2])
    >>> isinstance(reader, RandomSequentialReader)
    True
    >>> reader.readall()
    [1, 2]
    >>> isinstance(wrap(iter([])), SequentialReader)
    True
    >>> wrap(None)
    Traceback (most recent call last):
        ...
    TypeError: must be a Iterable, got <class 'NoneType'>

    .. versionadded:: 3.4
    """
    # if it is a reader already, just return it
    if isinstance(iterable, Reader):
        return iterable

    # async reader
    if isinstance(iterable, AsyncIterable):
        return AsyncSequentialReader(iterable, count=None)

    if not isinstance(iterable, Iterable):
        raise TypeError("must be a Iterable, got {}".format(type(iterable)))
    if isinstance(iterable, Sequence):
        count = len(iterable)
        return RandomSequentialReader(count,
                                      lambda start, end: iterable[start:end],
                                      max_per_read=max(count, 1))
    # maybe a generator/iterator
    return SequentialReader(iterable, count=None)
