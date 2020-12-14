class TipsManager(object):
    """在合适的时候展示一些使用 Tip"""

    tips = [
        '你知道 mpris2 插件可以配合 osdlyrics 使用吗?',
        '双击歌手就可以浏览歌手的热门歌曲',
        '您可以自定义主题哦',
        '您有任何有关问题都可以上项目主页反馈哦',
        'Ctrl + F: 搜索快捷键, J, K 可以上下移动光标',
    ]

    def __init__(self, app):
        self._app = app

    def show_random_tip(self):
        pass
