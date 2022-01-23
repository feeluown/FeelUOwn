import warnings

# For backward compat.
from feeluown.gui import PlaylistUiManager  # noqa


warnings.warn('Please import PlaylistUiManager from feeluown.gui',
              DeprecationWarning, stacklevel=2)
