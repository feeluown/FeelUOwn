开发最佳实践
============


代码风格
--------

注释
~~~~

- 注释统一用英文（老的中文注释应该逐渐更改）
- docstring 使用 `Sphinx docstring format`_
- FIXME, TODO, and HELP

  - FIXME: 开发者明确知道某个地方代码不优雅
  - HELP: 开发者写了一段自己不太理解，但是可以正确工作的代码
  - TODO: 一些可以以后完成的事情
  - 暂时不推荐使用 NOTE 标记

测试
~~~~

- feeluown 包相关代码都应该添加相应测试。
- GUI 改动优先运行 focused GUI/library 测试。如果本地环境中完整 Qt/mpv pytest
  不稳定，应在 PR 说明中明确记录。

错误处理
~~~~~~~~

- Qt 中同步调用资源提供方接口时，都应该处理 Exception 异常，否则应用可能会 crash。
- 避免用宽泛的 fallback 分支隐藏失败。如果输入契约不符合预期，应通过明确的
  类型或结构检查尽早失败。

特殊风格
~~~~~~~~

- 标记了 alpha 的函数和类，它们的设计都是不确定的，外部应该尽少依赖。

类
~~

- Qt Widget 的子类的 UI 相关设置初始化应该放在 ``_setup_ui`` 函数中。
- 信号的 slot 方法应该设为 protected 方法。
- 类的 public 方法放在类的前面，protected 和 private 方法放在类的最后面，
  ``_setup_ui`` 函数除外。
- QWidget 子类最好不要有 async 方法，因为目前无法很好的为它编写相关单元测试。


UI 设计
-------

- 设计 UI 时要考虑 Linux、Windows、macOS 的兼容性。颜色应尽量来自系统
  调色板，比如 ``QPalette`` 的 ``Window``、``Base``、``Text``、
  ``WindowText``、``Highlight`` 等角色，而不是硬编码某一种颜色。


运行时调试
----------

- 可以用 ``fuo exec`` 连接正在运行的应用，执行 Python 代码来调试界面状态、
  构造测试场景或读取对象属性。启动应用时不要使用 ``-ns``，因为它表示
  no-server，``fuo exec`` 将无法连接到应用。
- ``fuo exec`` 支持从 stdin 接收多行 Python 代码。调试复杂流程时优先使用
  这种方式，避免在 shell 参数中处理繁琐的引号和转义。示例::

    # 在 tmux 中启动 GUI，并打开 server
    uv run fuo -vv

    # 在另一个 shell 中注入多行 Python 代码
    uv run fuo exec <<'EOF'
    print(type(app).__name__)
    print(app.ui)
    EOF


工程经验
--------

- API 命名应优先表达语义，而不是绑定某个调用场景。例如
  ``show_cover_with_source(artwork, source, uid)`` 比编码某个具体 caller
  上下文的名字更清晰。
- 封面和图片加载应保持清晰边界：数据/适配层负责把 ``(url, source)`` 转换为
  ``Media``，widget 层尽量直接消费 ``Media``。
- 删除 helper 函数前，先用 ``rg`` 明确检查使用点。如果它仍被多个 GUI 路径共享，
  应保留这个 helper。
- 通过 ``gh`` 创建或更新 PR 描述时，优先使用 ``--body-file``，或使用 GraphQL
  ``updatePullRequest`` 并从文件读取正文；避免在命令行里内联转义 ``\n``，
  否则 PR 描述可能出现字面量 ``\n``。


.. _Sphinx docstring format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format
