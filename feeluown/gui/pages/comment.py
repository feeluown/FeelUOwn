from feeluown.utils import aio
from feeluown.library import ProviderFlags as PF
from feeluown.gui.page_containers.table import Renderer


async def render(req, **kwargs):
    app = req.ctx['app']
    song = req.ctx['model']

    if not app.library.check_flags_by_model(song, PF.hot_comments):
        return

    comments = await aio.run_in_executor(None, app.library.song_list_hot_comments, song)
    await app.ui.table_container.set_renderer(HotCommentsRenderer(song, comments))


class HotCommentsRenderer(Renderer):
    def __init__(self, song, comments):
        self._song = song
        self._comments = comments

    async def render(self):
        song = self._song
        song_str = f'{song.title_display} - {song.artists_name_display}'
        self.meta_widget.title = f'“{song_str}”的热门评论'
        self.meta_widget.show()
        self.show_comments(self._comments)
