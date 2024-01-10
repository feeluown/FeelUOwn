# -*- coding: utf-8 -*-

"""
feeluown.library
~~~~~~~~~~~~~~~~

"""
from abc import ABC, abstractmethod
from contextlib import contextmanager


class AbstractProvider(ABC):
    """abstract music resource provider
    """

    def __init__(self):
        self._user = None

    @property
    @abstractmethod
    def identifier(self):
        """provider identify"""

    @property
    @abstractmethod
    def name(self):
        """provider name"""

    @contextmanager
    def auth_as(self, user):
        """auth as a user temporarily

        Usage::

            with auth_as(user):
                ...
        """
        old_user = self._user
        self.auth(user)
        try:
            yield
        finally:
            self.auth(old_user)

    def auth(self, user):
        """use provider as a specific user"""
        self._user = user

    def search(self, *args, **kwargs):
        pass
