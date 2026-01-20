import random

from feeluown.utils import aio
from feeluown.app import App
from feeluown.i18n import t

# (nickname, name), no order.
# Write your Chinese(or other languages) name if you want.
Contributors = [
    ("cosven", "Shaowen Yin"),
    ("felixonmars", ""),
    ("PhotonQuantum", ""),
    ("wuliaotc", ""),
    ("cyliuu", ""),
    ("light4", ""),
    ("hjlarry", ""),
    ("sbwtw", ""),
    ("oryxfea", ""),
    ("poly000", ""),
    ("BruceZhang1993", ""),
    ("cposture", ""),
    ("helinb", ""),
    ("Yexiaoxing", ""),
    ("albertofwb", ""),
    ("catsout", ""),
    ("Torxed", ""),
    ("RealXuChe", ""),
    ("rapiz1", ""),
    ("Heersin", ""),
    ("chen-chao", ""),
    ("keter42", ""),
    ("timgates42", ""),
    ("junhan-z", ""),
    ("CareF", ""),
    ("berberman", ""),
    ("SaneBow", ""),
    ("wsyxbcl", ""),
    ("Thearas", ""),
    ("reaink", ""),
    ("wenLiangcan", ""),
    ("leedagee", ""),
    ("hanchanli", ""),
    ("xssss1", ""),
    ("williamherry", ""),
    ("seiuneko", ""),
    ("emmanuel-ferdman", ""),
    ("c-xk", "Shinka"),
    ("w568w", ""),
    ("mokurin000", "莯凛"),
]


class TipsManager:
    """Display some usage tips at appropriate times."""

    tips = [
        t("tips-osdlyrics"),
        t("tips-search-shortcut", shortcut="Ctrl + F"),
        t("tips-show-more-tips"),
        t("tips-album-original-image"),
        t("tips-track-drag-to-playlist"),
        t("tips-common-tooltip"),
        t("tips-watch-mode"),
    ]

    def __init__(self, app: App):
        self._app = app
        self._app.started.connect(self.show_random_after_5s)

    def show_random(self):
        if random.randint(0, 10) < 5:
            self._app.show_msg(random.choice(self.tips), timeout=2500)
        else:
            contributor = random.choice(Contributors)
            nickname, name = contributor
            if name:
                user = f"{name} (@{nickname})"
            else:
                user = f"@{nickname}"
            msg = t("thanks-contributor", user=user)
            self._app.show_msg(msg, timeout=2500)

    def show_random_after_5s(self, *_):
        async def task():
            await aio.sleep(5)
            self.show_random()

        aio.run_afn(task)
