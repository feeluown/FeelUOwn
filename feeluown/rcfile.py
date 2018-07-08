import os


DEFAULT_RCFILE_PATH = os.path.expanduser('~/.fuorc')


def load_rcfile(app, rcfile_path=DEFAULT_RCFILE_PATH):
    if not os.path.exists(DEFAULT_RCFILE_PATH):
        return

    g = {'app': app}
    with open(rcfile_path) as f:
        exec(f.read(), g)
