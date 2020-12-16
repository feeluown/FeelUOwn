import warnings

# for backward compact
from feeluown.library.library import *  # noqa


warnings.warn('use feeluown.library please',
              DeprecationWarning, stacklevel=2)
