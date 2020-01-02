import os


is_travis_env = os.environ.get('TEST_ENV') == 'travis'

cannot_play_audio = is_travis_env
cannot_run_qt_test = is_travis_env
