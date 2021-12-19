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
    """Set unknown field should cause no effects"""
    config.hey = 0
    with pytest.raises(AttributeError):
        config.hey


def test_config_set_subconfig(config):
    """Field is a config object and it should just works"""
    config.deffield('nowplaying', type_=Config)
    config.nowplaying = Config()
    config.nowplaying.deffield('control', type_=True, default=False)
    assert config.nowplaying.control is False
    config.nowplaying.control = True
    assert config.nowplaying.control is True
