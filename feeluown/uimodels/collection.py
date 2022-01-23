import warnings

# For backward compat.
from feeluown.gui import CollectionUiManager  # noqa


warnings.warn('Please import CollectionUiManager from feeluown.gui',
              DeprecationWarning, stacklevel=2)
