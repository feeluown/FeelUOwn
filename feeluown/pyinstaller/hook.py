import pathlib


def get_hook_dirs():
    hooks_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent / 'pyinstaller_hooks')
    return [hooks_dir]