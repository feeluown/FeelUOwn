class LibraryException(Exception):
    pass


class ProviderAlreadyExists(LibraryException):
    pass


class ProviderNotFound(LibraryException):
    pass


class ModelNotFound(LibraryException):
    """Model is not found.

    For example, a model identifier is invalid.
    """


class NotSupported(LibraryException):
    pass


class NoUserLoggedIn(LibraryException):
    pass


class MediaNotFound(LibraryException):
    pass
