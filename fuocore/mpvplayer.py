import warnings

from feeluown.player.mpvplayer import *  # noqa
from feeluown.player.mpvplayer import (  # noqa
    _mpv_set_property_string,
    _mpv_set_option_string,
)


warnings.warn('use feeluown.player.mpvplayer please',
              DeprecationWarning, stacklevel=2)
