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


def test_config_set_value_to_a_different_type(config):
    """Set field to unexpected type should not change the value"""
    config.VERBOSE = '2'
    assert config.VERBOSE == 1


def test_config_deffield_with_invalid_type(config):
    with pytest.raises(ValueError):
        config.deffield('hey', type_=int, default='x')


def test_config_deffield_with_invalid_default_value(config):
    with pytest.raises(ValueError):
        config.deffield('hey', type_=2, default=2)


def test_config_set_subconfig(config):
    """Field is a config object and it should just works"""
    config.deffield('nowplaying', type_=Config, default=Config())
    config.nowplaying = Config()
    config.nowplaying.deffield('control', type_=bool, default=False)
    assert config.nowplaying.control is False
    config.nowplaying.control = True
    assert config.nowplaying.control is True
