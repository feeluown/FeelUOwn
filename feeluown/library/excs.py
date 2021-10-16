class LibraryException(Exception):
    pass


class ResourceNotFound(LibraryException):
    pass


class ProviderAlreadyExists(LibraryException):
    pass


class ProviderNotFound(ResourceNotFound):
    pass


class ModelNotFound(ResourceNotFound):
    """Model is not found

    For example, a model identifier is invalid.

    .. versionadded:: 3.7.7
    """


class NotSupported(LibraryException):
    """Provider does not support the operation
    """


class NoUserLoggedIn(LibraryException):
    pass


class MediaNotFound(ResourceNotFound):
    pass
