import os


DEFAULT_RCFILE_PATH = os.path.expanduser('~/.fuorc')


def load_rcfile(rcfile_path=DEFAULT_RCFILE_PATH):
    with open(rcfile_path) as f:
        exec(f.read())
