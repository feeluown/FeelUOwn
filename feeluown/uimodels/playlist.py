"""
播放列表管理
~~~~~~~~~~~~~
"""

from feeluown.widgets.playlists import PlaylistsModel

from feeluown.models import PlaylistModel


class PlaylistUiItem(PlaylistModel):
    """
    根据目前经验，播放列表的相关操作最基本的就是几个：

    * 创建、删除
    * 添加、移除歌曲
    * 重命名
    * 点击展示这个歌单

    这些操作对各平台的播放列表、歌单来说，语义都是一致的，
    所以 PlaylistUiItem 暂时不提供 clicked 等操作信号。
    """
    pass


class PlaylistUiManager:
    def __init__(self, app):
        self._app = app
        self.model = PlaylistsModel(app)

    def add(self, playlist, is_fav=False):
        self.model.add(playlist, is_fav=is_fav)

    def clear(self):
        self.model.clear()
