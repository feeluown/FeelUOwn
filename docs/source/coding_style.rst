代码风格
================


注释
-------

- 注释统一用英文（老的中文注释应该逐渐更改）
- docstring 使用 `Sphinx docstring format`_
- FIXME, TODO, and HELP
  - FIXME: 开发者明确知道某个地方代码不优雅
  - HELP: 开发者写了一段自己不太理解，但是可以正确工作的代码
  - TODO: 一些可以以后完成的事情
  - 暂时不推荐使用 NOTE 标记

命名
-------


测试
--------

- fuocore 包相关代码都应该添加相应测试

错误处理
------------

日志和提示
-----------



特殊风格
-----------

- 标记了 alpha 的函数和类，它们的设计都是不确定的，外部应该尽少依赖


.. _Sphinx docstring format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format
