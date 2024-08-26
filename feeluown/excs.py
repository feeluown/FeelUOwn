"""
HELP: I do not know how to design exception classes,
as a result, these interfaces can be changed frequently.
"""
from enum import Enum

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
    class Reason(Enum):
        """
        .. versionadded:: v4.0
        """
        not_found = 'not_found'
        # The provider does implement corresponding protocol.
        not_supported = 'not_supported'

    def __init__(self, *args, reason=Reason.not_found, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reason = reason


class ProviderAlreadyRegistered(LibraryException):
    pass


class ModelNotFound(ResourceNotFound):
    """Model is not found

    For example, a model identifier is invalid.
    Maybe ResourceNotFound is enough and this exception should be removed.

    .. versionadded:: 3.7.7
    """


class MediaNotFound(ResourceNotFound):
    class Reason(Enum):
        not_found = 'not_found'
        # Song/video has children and children have medias. Song/video itself does
        # not have any media.
        check_children = 'check_children'

    def __init__(self, *args, reason=Reason.not_found, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reason = reason


class NoUserLoggedIn(LibraryException):
    """(DEPRECATED) return None when there is no user logged in"""
