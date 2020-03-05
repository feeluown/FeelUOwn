import time
from threading import RLock


_NOT_FOUND = object()


class cached_field:
    """like functools.cached_property, but designed for Model

    >>> class User:
    ...     @cached_field()
    ...     def playlists(self):
    ...         return [1, 2]
    ...
    >>> user = User()
    >>> user2 = User()
    >>> user.playlists = None
    >>> user.playlists
    [1, 2]
    >>> user.playlists = [3, 4]
    >>> user.playlists
    [3, 4]
    >>> user2.playlists
    [1, 2]
    """
    def __init__(self, ttl=None):
        self._ttl = ttl
        self.lock = RLock()

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, obj, owner):
        if obj is None:  # Class.field
            return self

        try:
            # XXX: maybe we can use use a special attribute
            # (such as _cached_{name}) to store the cache value
            # instead of __dict__
            cache = obj.__dict__
        except AttributeError:
            raise TypeError("obj should have __dict__ attribute") from None

        cache_key = '_cache_' + self.func.__name__
        datum = cache.get(cache_key, _NOT_FOUND)
        if self._should_refresh_datum(datum):
            with self.lock:
                # check if another thread filled cache while we awaited lock
                datum = cache.get(cache_key, _NOT_FOUND)
                if self._should_refresh_datum(datum):
                    value = self.func(obj)
                    cache[cache_key] = datum = self._gen_datum(value)
        return datum[1]

    def __set__(self, obj, value):
        cache_key = '_cache_' + self.func.__name__
        obj.__dict__[cache_key] = self._gen_datum(value)

    def _should_refresh_datum(self, datum):
        return (
            datum is _NOT_FOUND or  # not initialized
            datum[1] is None or     # None implies that the value can be refreshed
            datum[0] is not None and datum[0] < time.time()  # expired
        )

    def _gen_datum(self, value):
        if self._ttl is None:
            expired_at = None
        else:
            expired_at = int(time.time()) + self._ttl
        return (expired_at, value)
