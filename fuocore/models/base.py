import time


class cached_field:
    """like functools.cached_property, but designed for Model

    >>> class User:
    ...     @cached_field()
    ...     def playlists(self):
    ...         return [1, 2]
    ...
    >>> user = User()
    >>> user.playlists = None
    >>> user.playlists
    [1, 2]
    >>> user.playlists = [3, 4]
    >>> user.playlists
    [3, 4]
    """
    def __init__(self, ttl=None):
        self._ttl = ttl
        # None means that this field is not initialized
        self._value = None
        self._updated_at = None

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, obj, objtype=None):
        if self._value is not None:
            now = int(time.time())
            if self._ttl is None or self._updated_at + self._ttl > now:
                return self._value
        value = self.func(obj)
        self.__set__(obj, value)
        return self._value

    def __set__(self, obj, value):
        self._value = value
        self._updated_at = int(time.time())
