import os


is_travis_env = os.environ.get('TEST_ENV') == 'travis'
