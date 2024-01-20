# Old code imports these exceptions from this module
from feeluown.excs import (  # noqa
    LibraryException,
    ResourceNotFound,
    # FIXME: ProviderAlreadyExists should be renamed to ProviderAlreadyRegistered
    ProviderAlreadyRegistered as ProviderAlreadyExists,
    ModelNotFound,
    NoUserLoggedIn,
    MediaNotFound,
)  # noqa
