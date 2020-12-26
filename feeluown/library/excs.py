class LibraryException(Exception):
    pass


class ModelUpgradeFailed(LibraryException):
    pass


class MediaNotFound(LibraryException):
    pass
