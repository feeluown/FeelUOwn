"""
HELP: I do not know how to design exception classes,
as a result, these interfaces can be changed frequently.
"""

from requests.exceptions import RequestException


class FuoException(Exception):
    pass


class LibraryException(FuoException):
    pass


class ProviderIOError(LibraryException, RequestException):
    """Read/write data from/to provider failed

    currently, all providers use requests to send http request,
    and many Requestexception are not catched, so ProviderIOError
    inherit RequestException.
    """

    def __init__(self, message='', provider=None):
        super().__init__(message)

        self.message = message
        self.provider = provider

    def __str__(self):
        if self.provider is None:
            return self.message
        return '[{}] {}'.format(self.provider, self.message)


class CreateReaderFailed(ProviderIOError):
    """(DEPRECATED) use ProviderIOError instead"""


class ReaderException(ProviderIOError):
    """(DEPRECATED) use ProviderIOError instead"""


class ReadFailed(ProviderIOError):
    """(DEPRECATED) use ProviderIOError instead"""


class ResourceNotFound(LibraryException):
    pass


class ProviderAlreadyRegistered(LibraryException):
    pass


class ProviderNotFound(ResourceNotFound):
    pass


class ModelNotFound(ResourceNotFound):
    """Model is not found

    For example, a model identifier is invalid.

    .. versionadded:: 3.7.7
    """


class ModelCannotUpgrade(LibraryException):
    """Model cannot be upgraded

    .. versionadded:: 3.8.9
    """


class NotSupported(LibraryException):
    """Provider does not support the operation
    """


class MediaNotFound(ResourceNotFound):
    pass


class NoUserLoggedIn(LibraryException):
    """(DEPRECATED) return None when there is no user logged in"""
