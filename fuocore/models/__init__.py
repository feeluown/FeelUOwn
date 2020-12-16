import warnings

from feeluown.utils.reader import SequentialReader as GeneratorProxy  # noqa, for backward compatible
from feeluown.models import *  # noqa


warnings.warn('use feeluown.models please',
              DeprecationWarning, stacklevel=2)
