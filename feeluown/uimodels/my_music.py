import warnings

# For backward compat.
from feeluown.gui import MyMusicUiManager  # noqa


warnings.warn('Please import MyMusicUiManager from feeluown.gui',
              DeprecationWarning, stacklevel=2)
