import time


class cached_property_descriptor:
    """
    If a field is initialized by a individual request, we will have
    such code::

        class Model:

            def f(self):
                if hasattr(self, '_f'):
                    return self._f
                value = request()
                self.f = value
                return self.f

            @f.setter
            def f(self, value):
                self._f = value

    By using dynamic_property, we can simplify it to::

        class Model:
            def get_f_value(self):
                pass

            f = dynamic_property(get_f_value)
    """
    def __init__(self, get_value_func, ttl=None):
        self._ttl = ttl
        self._value = None
        self._updated_at = None
        self._get_value_func = get_value_func

    def __get__(self, obj, objtype=None):
        if self._value is not None:
            now = int(time.time())
            if self._ttl is None or self._updated_at + self._ttl > now:
                return self._value
        value = self._get_value_func(obj)
        self.__set__(obj, value)
        return self._value

    def __set__(self, obj, value):
        self._value = value
        self._updated_at = int(time.time())


def cached_property(ttl=None):
    """
    >>> class User:
    ...     @cached_property()
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

    def wrapper(func):
        return cached_property_descriptor(func, ttl=ttl)

    return wrapper
