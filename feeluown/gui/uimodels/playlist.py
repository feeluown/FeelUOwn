"""
Playlist Management
~~~~~~~~~~~~~
"""

from feeluown.gui.widgets.playlists import PlaylistsModel

from feeluown.library import PlaylistModel


class PlaylistUiItem(PlaylistModel):
    """
Based on current experience, the most basic operations related to playlists are:

    * Creating, deleting
    * Adding, removing songs
    * Renaming
    * Clicking to display this playlist

    These operations have consistent semantics across platforms,
    so PlaylistUiItem does not provide signals like clicked for now.
    """


class PlaylistUiManager:
    def __init__(self, app):
        self._app = app
        self.model = PlaylistsModel(app)

    def add(self, playlist, is_fav=False):
        self.model.add(playlist, is_fav=is_fav)

    def clear(self):
        self.model.clear()
