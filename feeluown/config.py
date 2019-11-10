import logging
import warnings
from collections import namedtuple

logger = logging.getLogger(__name__)


Field = namedtuple('Field', ('name', 'type_', 'default', 'desc', 'warn'))


class Config:
    """配置模块

    用户可以在 rc 文件中配置各个选项的值
    """

    def __init__(self):
        object.__setattr__(self, '_fields', {})

    def __getattr__(self, name):
        # tips: 这里不能用 getattr 来获取值, 否则会死循环
        if name == '_fields':
            return object.__getattribute__(self, '_fields')
        if name in self._fields:
            try:
                object.__getattribute__(self, name)
            except AttributeError:
                return self._fields[name].default
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in self._fields:
            field = self._fields[name]
            if field.warn is not None:
                warnings.warn('Config field({}): {}'.format(name, field.warn),
                              stacklevel=2)
            # TODO: 校验值类型
            object.__setattr__(self, name, value)
        else:
            logger.warning('Assign to an undeclared config key.')

    def deffield(self, name, type_=None, default=None, desc='', warn=None):
        """定义字段信息"""
        if name not in self._fields:
            self._fields[name] = Field(name=name,
                                       type_=type_,
                                       default=default,
                                       desc=desc,
                                       warn=warn)
        else:
            raise ValueError('Field({}) is already defined.'.format(name))
