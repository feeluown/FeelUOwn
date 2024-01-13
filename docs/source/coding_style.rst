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

- feeluown 包相关代码都应该添加相应测试

错误处理
------------

- Qt 中同步调用资源提供方接口时，都应该处理 Exception 异常，否则应用可能会 crash

日志和提示
-----------

特殊风格
-----------

- 标记了 alpha 的函数和类，它们的设计都是不确定的，外部应该尽少依赖

类
-----------

- Qt Widget 的子类的 UI 相关设置初始化应该放在 ``_setup_ui`` 函数中
- 信号的 slot 方法应该设为 protected 方法
- 类的 public 方法放在类的前面，protected 和 private 方法放在类的最后面，
  ``_setup_ui`` 函数除外
- QWidget 子类最好不要有 async 方法，因为目前无法很好的为它编写相关单元测试



.. _Sphinx docstring format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format
