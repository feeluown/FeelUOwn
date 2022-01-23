import warnings

# For backward compat.
from feeluown.gui import ProviderUiManager  # noqa


warnings.warn('Please import ProviderUiManager from feeluown.gui',
              DeprecationWarning, stacklevel=2)
