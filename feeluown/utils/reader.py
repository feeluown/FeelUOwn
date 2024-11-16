import logging
from abc import ABCMeta, abstractmethod
from typing import (
    List,
    Generic,
    TypeVar,
    Optional,
    Callable,
    Tuple,
    Iterable,
    cast,
    Sequence,
    AsyncIterable,
)
from threading import Lock

logger = logging.getLogger(__name__)

__all__ = (
    'create_reader',
    'SequentialReader',
    'RandomSequentialReader',
    'Reader',
    'AsyncReader',
    # Below are deprecated.
    'RandomReader',
    'wrap',
)

T = TypeVar("T")


class ReaderException(Exception):
    pass


class CantReadAll(ReaderException):
    pass


class Reader(Generic[T], metaclass=ABCMeta):
    """Base reader class.

    This class is mainly designed for the following use case::

        Provider often splits resource which has large body to chunks, such as
        a large playlist with 10k songs, the client need to send several request
        to fetch the whole playlist. Generally, we call this design Pagination.
        Moreover, different provider has different pagination API. We want a
        unified API, so we create the Reader class.

    Note ``read_*`` method may raise *ANY* exception. In practice, the caller
    should know what exception is possible to happen. For example, for the
    upper use case, ProviderIOError is possible to happen and others are not
    supposed.
    """

    @property
    @abstractmethod
    def count(self) -> int:
        """Total number of objects reader can read."""

    @abstractmethod
    def read_range(self, start: int, end: int) -> List[T]:
        """Read objects in range [start, end)."""

    @abstractmethod
    def read(self, index) -> T:
        """Read object by index.

        :raises IndexError:
        """

    @abstractmethod
    def readall(self) -> List[T]:
        """Read all objects.

        :raises CantReadAll:

        .. versionchanged:: 3.8.10
           Raise CantReadAll instead of ReadFailed exception. ReadFailed inherits
           from ProviderIOError, but Reader and ProviderIOError should not be coupled.
        """

    @abstractmethod
    def _read_next(self) -> T:
        """Read next object. Only for internal usage."""

    def __iter__(self):
        return self

    def __next__(self) -> T:
        """

        .. versionchanged:: 3.8.10
           Do not handle any exception here. The caller should be responsible to
           handle exceptions.
        """
        return self._read_next()


class SequentialReader(Reader[T]):
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

    def __init__(self, g, count: Optional[int], offset: int = 0):
        """init

        :param g: Python generator
        :param offset: current offset
        :param count: total count. count can be None, which means the
                      total count is unknown. When it is unknown, be
                      CAREFUL to use list(reader).
        """
        super().__init__()
        self._g = g
        self._count = count
        self.offset = offset
        self._objects: List[T] = []
        self._lock = Lock()

    @property
    def count(self):
        return self._count

    def readall(self) -> List[T]:
        if self._count is None:
            raise CantReadAll("can't readall when count is unknown")
        list(self)
        return self._objects

    def read_range(self, start, end) -> List[T]:
        assert 0 <= start < end
        while len(self._objects) < end:
            try:
                next(self)
            except StopIteration:
                break
        return self._objects[start:end]

    def read(self, index):
        self.read_range(index, index+1)
        return self._objects[index]

    def _read_next(self) -> T:
        if self._count is None or self.offset < self.count:
            try:
                with self._lock:
                    obj = next(self._g)
            except StopIteration:
                if self._count is None:
                    self._count = self.offset + 1
                raise
        else:
            raise StopIteration
        self.offset += 1
        self._objects.append(obj)
        return obj


class RandomSequentialReader(Reader[T]):

    def __init__(self,
                 count,
                 read_func: Callable[[int, int], Iterable[T]],
                 max_per_read=100):
        """random reader constructor

        :param int count: total number of objects
        :param function read_func: func(start: int, end: int) -> list
        :param int max_per_read: max count per read, it must big than 0
        """
        self.offset = 0
        self._count = count
        self._ranges: List[Tuple[int, int]] = []  # list of tuple
        self._objects: List[Optional[T]] = [None] * count
        self._read_func = read_func
        self._lock = Lock()

        assert max_per_read > 0, 'max_per_read must big than 0'
        self._max_per_read = max_per_read

    @property
    def count(self):
        return self._count

    def read(self, index):
        """read object by index

        If the object is not already read, this method may trigger IO operation.
        """
        yes, r = self._has_index(index)
        if yes:
            return self._objects[index]
        self._read_range(*r)
        return self._objects[index]

    def readall(self) -> List[T]:
        """read all objects

        :return list: list of objects
        :raises ReadFailed:
        """
        # all objects have been read
        if len(self._ranges) == 1 and self._ranges[0] == (0, self._count):
            return cast(List[T], self._objects)

        start = 0
        end = 0
        count = self._count
        while end < count:
            end = min(count, end + self._max_per_read)
            self._read_range(start, end)
            start = end
        return cast(List[T], self._objects)

    # def explain_readall(self):
    #     read_times = self._count / self._max_per_read
    #     if self._count % self._max_per_read > 0:
    #         read_times += 1
    #     return {'count': self._count,
    #             'max_per_read': self._max_per_read,
    #             'read_times': read_times}

    def read_range(self, start, end) -> List[T]:
        self._read_range(start, end)
        return cast(List[T], self._objects[start:end])

    def _read_range(self, start, end):
        # Though this method is thread safe now, _read_range_unsafe may read
        # the same range multiple times.
        with self._lock:
            self._read_range_unsafe(start, end)

    def _read_range_unsafe(self, start, end):
        assert start <= end, 'start should less than end'
        logger.debug('trigger read_func(%d, %d)', start, end)
        objs = list(self._read_func(start, end))
        actual = len(objs)
        self._objects[start:start + actual] = objs
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
            # default read range [index, min(index + max_per_read, self._count))
            left_index = index
            right_index = min(index + self._max_per_read, self._count)
            # trick: read as much as possible at a time to improve performance
            if gt_index is not None:
                if self._count - gt_index < self._max_per_read:
                    left_index = gt_index
                    right_index = self._count
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

    def _read_next(self):
        if self.offset >= self._count:
            raise StopIteration
        obj = self.read(self.offset)
        self.offset += 1
        return obj


RandomReader = RandomSequentialReader  # For backward compatibility.


class AsyncReader:
    """Async version of reader.

    .. versionadded:: 3.8.10
    """

    pass


class AsyncSequentialReader(AsyncReader):

    def __init__(self, g, count, offset=0):
        """init

        :param g: Python generator
        :param offset: current offset
        :param count: total count. count can be None, which means the
                      total count is unknown. When it is unknown, be
                      CAREFUL to use list(reader).
        """
        self._g = g
        self._count = count
        self.offset = offset
        self._objects = []

    @property
    def count(self):
        return self._count

    async def a_readall(self):
        if self._count is None:
            raise CantReadAll("can't readall when count is unknown")
        async for _ in self:
            pass
        return self._objects

    async def a_read_next(self):
        if self._count is None or self.offset < self.count:
            try:
                obj = await self._g.asend(None)
            except StopAsyncIteration:
                if self._count is None:
                    self._count = self.offset + 1
                raise
        else:
            raise StopAsyncIteration
        self.offset += 1
        self._objects.append(obj)
        return obj

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.a_read_next()
        except StopAsyncIteration:
            raise


def wrap(iterable):
    """

    .. versionadded:: 3.4
    .. deprecated:: 3.7.7
       Use :func:`create_reader` instead.
    """
    # if it is a reader already, just return it
    if isinstance(iterable, Reader):
        return iterable

    # async reader
    if isinstance(iterable, AsyncIterable):
        return AsyncSequentialReader(iterable, count=None)

    if not isinstance(iterable, Iterable):
        raise TypeError(f'must be a Iterable, got {type(iterable)}')
    if isinstance(iterable, Sequence):
        count = len(iterable)
        return RandomSequentialReader(count,
                                      lambda start, end: iterable[start:end],
                                      max_per_read=max(count, 1))
    # maybe a generator/iterator
    return SequentialReader(iterable, count=None)


def create_reader(iterable):
    """Create a reader from an iterable.

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

    .. versionadded:: 3.7.7
    """
    return wrap(iterable)
