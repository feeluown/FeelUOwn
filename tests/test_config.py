import pytest

from feeluown.config import Config


@pytest.fixture
def config():
    c = Config()
    c.deffield('VERBOSE', type_=int, default=1)
    return c


def test_config_set_known_field(config):
    config.VERBOSE = 2
    # The value should be changed.
    assert config.VERBOSE == 2


def test_config_set_unknown_field(config):
    """
    Set unknown field should cause no effects.
    Access unknown field should return a Config object.
    """
    config.hey = 0
    assert isinstance(config.hey, Config)
    config.plugin.X = 0  # should not raise error
    assert isinstance(config.plugin.X, Config)


def test_config_set_subconfig(config):
    """Field is a config object and it should just works"""
    config.deffield('nowplaying', type_=Config)
    config.nowplaying = Config()
    config.nowplaying.deffield('control', type_=True, default=False)
    assert config.nowplaying.control is False
    config.nowplaying.control = True
    assert config.nowplaying.control is True
