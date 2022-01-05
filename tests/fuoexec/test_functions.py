import pytest

from feeluown.fuoexec.functions import source
from feeluown.fuoexec.fuoexec import fuoexec_get_globals, fuoexec_init
from feeluown.fuoexec.signal_manager import signal_mgr
from feeluown.utils.dispatch import Signal


rcfile_content = """
def hey(*args):
    print('hey!!!')

when('app.initialized', hey, use_symbol=True, aioqueue=False)
"""


@pytest.fixture
def load_rcfile(tmp_path):
    rcfile = tmp_path / 'rcfile'
    rcfile.touch()
    with rcfile.open('w') as f:
        f.write(rcfile_content)
    source(str(rcfile))


@pytest.fixture
def reinit_fuoexec(app_mock):
    """
    fuoexec can be only initialized once, but we should initialize it for
    each test case. This function does this trick.
    """
    g = fuoexec_get_globals().copy()
    app_mock.initialized = Signal()
    fuoexec_init(app_mock)
    yield
    fuoexec_get_globals().clear()
    fuoexec_get_globals().update(g)
    signal_mgr.initialized = False
    signal_mgr.signal_connectors.clear()


def test_source(reinit_fuoexec, load_rcfile):
    assert 'hey' in fuoexec_get_globals()


def test_add_hook(reinit_fuoexec, load_rcfile, mocker):
    g = fuoexec_get_globals()
    mock_hey = mocker.Mock()
    g['hey'] = mock_hey
    g['app'].initialized.emit()
    # The function is changed, symbol should refers to the new function.
    # Therefore, the new function should be called.
    assert mock_hey.called
