import pathlib


def get_hook_dirs():
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    hooks_dir = str(root / 'pyinstaller_hooks')
    return [hooks_dir]
