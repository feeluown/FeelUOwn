from typing import Optional
import logging
import warnings
from collections import namedtuple


logger = logging.getLogger(__name__)


Field = namedtuple('Field', ('name', 'type_', 'default', 'desc', 'warn'))


class Config:
    """配置模块

    用户可以在 rc 文件中配置各个选项的值
    """

    def __init__(self, name: str = 'config', parent: Optional['Config'] = None):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_fields', {})
        object.__setattr__(self, '_undeclared_fields', {})

    def __getattr__(self, name):
        # tips: 这里不能用 getattr 来获取值, 否则会死循环
        if name in ('_fields', '_parent', '_name', '_undeclared_fields'):
            return object.__getattribute__(self, name)
        if name in self._fields:
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return self._fields[name].default
        elif name in self._undeclared_fields:
            return self._undeclared_fields[name]

        # Requirement:
        #   User may define config like
        #       app.plugin.X = Y
        #   When 'plugin' is not installed, such config should not raise an error.
        # To achieve this, return a subconfig when accessing an undeclared key.
        logger.warning(f'Undeclared subconfig: {self.fullname}.{name}')
        tmpconfig = Config(name=name, parent=self)
        self._undeclared_fields[name] = tmpconfig
        return tmpconfig

    def __setattr__(self, name, value):
        if name in self._fields:
            field = self._fields[name]
            if field.warn is not None:
                warnings.warn('Config field({}): {}'.format(name, field.warn),
                              stacklevel=2)
            # TODO: 校验值类型
            object.__setattr__(self, name, value)
        else:
            logger.warning(f'Assign to an undeclared config key: {self.fullname}.{name}')

    @property
    def fullname(self) -> str:
        if self._parent is None:
            return self._name
        return f'{self._parent.fullname}.{self._name}'

    def deffield(self, name, type_=None, default=None, desc='', warn=None):
        """Define a configuration field

        :param str name: the field name. It SHOULD be capitalized except the field
            refers to a sub-config.
        :param type_: feild type.
        :param default: default value for the field.
        :param desc: description for the field.
        :param warn: if field is deprecated, set a warn message.
        """
        if name not in self._fields:
            self._fields[name] = Field(name=name,
                                       type_=type_,
                                       default=default,
                                       desc=desc,
                                       warn=warn)
        else:
            raise ValueError('Field({}) is already defined.'.format(name))
