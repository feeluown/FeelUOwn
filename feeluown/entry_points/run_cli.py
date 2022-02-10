from feeluown.utils import aio
from feeluown.cli import climain


def run_cli(args):
    aio.run(climain(args))
