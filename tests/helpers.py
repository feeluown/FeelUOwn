import os


is_travis_env = os.environ.get('TEST_ENV') == 'travis'

cannot_play_audio = is_travis_env

# By set QT_QPA_PLATFORM=offscreen, qt widgets can run on various CI.
cannot_run_qt_test = False
