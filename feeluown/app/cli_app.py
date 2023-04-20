from feeluown.utils import aio
from .app import App


class CliApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        super().initialize()

    def run(self):
        super().run()

        # oncemain should be moved from feeluown/cli to feeluown/app,
        # However, it depends on cli logic temporarily. If there is
        # an common module for these cli logic, oncemain can be moved.
        from feeluown.cli import oncemain  # pylint: disable=cyclic-import

        aio.run_afn(oncemain, self)
