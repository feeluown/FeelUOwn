"""
HELP: I do not know how to design exception classes,
as a result, these interfaces can be changed frequently.
"""


class FuoException(Exception):
    pass


class ProviderIOError(FuoException):
    """Read/write data from/to provider failed"""

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
