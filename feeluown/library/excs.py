class LibraryException(Exception):
    pass


class ProviderAlreadyExists(LibraryException):
    pass


class ProviderNotFound(LibraryException):
    pass


class NotSupported(LibraryException):
    pass


class NoUserLoggedIn(LibraryException):
    pass


class MediaNotFound(LibraryException):
    pass
