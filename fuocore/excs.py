class FuoException(Exception):
    pass


class CreateReaderFailed(FuoException):
    pass


class ReaderException(FuoException):
    pass


class ReadFailed(ReaderException):
    pass
