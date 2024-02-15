"""
A component is a certain widget depends on `feeluown.app.App` object.
In other words, a component is tightly coupled with application logic.
"""

from .avatar import Avatar  # noqa
from .btns import *  # noqa
from .menu import SongMenuInitializer  # noqa
from .line_song import LineSongLabel  # noqa
from .playlist_btn import PlaylistButton  # noqa
from .volume_slider import *  # noqa
from .song_tag import SongSourceTag  # noqa
from .collections import CollectionListView  # noqa
from .player_progress import PlayerProgressSliderAndLabel  # noqa
