import random

from feeluown.utils import aio
from feeluown.app import App


class TipsManager:
    """在合适的时候展示一些使用 Tip"""

    tips = [
        '你知道 FeelUOwn 可以配合 osdlyrics 使用吗?',
        '搜索快捷键是 Ctrl + F',
        "在搜索框输入“>>> app.tips_mgr.show_random()”查看更多 Tips",
        '专辑图片上右键可以查看原图哦 ~',
        '可以拖动歌曲来将歌曲添加到歌单呐！',
        '鼠标悬浮或右键常有惊喜 ~',
        '开启 watch 模式一边看 MV，一边工作学习香不香？'
    ]

    def __init__(self, app: App):
        self._app = app
        self._app.started.connect(self.show_random_after_5s)

    def show_random(self):
        self._app.show_msg(random.choice(self.tips), timeout=2500)

    def show_random_after_5s(self, *_):
        async def task():
            await aio.sleep(5)
            self.show_random()

        aio.run_afn(task)
