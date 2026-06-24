内存问题调试
============

FeelUOwn 长时间运行后内存偏高时，先用成熟 profiler 采证，不在应用里维护自研采样器。
推荐主工具是 `Memray <https://bloomberg.github.io/memray/>`_。它能记录 Python、
C 扩展和解释器层面的内存分配，适合区分 Python 代码、Qt 绑定、mpv 相关扩展和其它 native
分配的影响。

.. note::

   Memray 支持 Linux 和 macOS。Windows 上先用系统任务管理器、Process Explorer 或
   Python 层工具收集现象，再到 Linux/macOS 环境做 Memray 复现。

基本流程
--------

1. 先测运行时 baseline。对 GUI 内存问题，先测最小 Qt 程序，再测 FeelUOwn 的增量。
2. 记录系统、Python 版本、Qt 版本、插件列表和启动命令。
3. 用 Memray 启动 FeelUOwn 并复现内存增长。
4. 生成 flamegraph 或 table 报告。
5. 如果 Memray 报告里 Python/native 分配不增长，但 RSS 仍增长，再排查 QtWebEngine 子进程、
   mpv、系统图形栈或插件外部进程。

最小 Qt baseline
----------------

分析 macOS 上的 Qt GUI 内存时，不要直接从 FeelUOwn 进程开始下结论。
先启动一个最小可见 Qt 窗口，并用 ``vmmap`` 记录 baseline：

.. code-block:: bash

   cat >/tmp/minimal_qt_window.py <<'PY'
   import time
   from PyQt6.QtWidgets import QApplication, QWidget

   app = QApplication([])
   widget = QWidget()
   widget.resize(320, 200)
   widget.show()
   app.processEvents()
   print("ready", flush=True)
   time.sleep(120)
   PY

   python3 /tmp/minimal_qt_window.py &
   pid=$!
   sleep 3
   vmmap -summary "$pid" > /tmp/minimal_qt_window.vmmap

参考值只用于判断量级，具体数值会随 macOS、Qt、Python 和显示环境变化。本机一次验证中：

- ``QApplication + QWidget.show()``：``Physical footprint`` 约 25 MB，
  ``TOTAL resident`` 约 415 MB，``Writable resident`` 约 18 MB。
- ``QApplication + QSystemTrayIcon.show()``：``Physical footprint`` 约 20 MB，
  ``TOTAL resident`` 约 405 MB，``Writable resident`` 约 13 MB。
- 按 ``vmmap`` 的 ``SM=PRV`` resident 粗略估算，最小可见 Qt 窗口的 USS 下界约 17 MB；
  如果再加上 ``SM=COW`` dirty page，私有 charge 约 23 MB。

这说明在 macOS 上，一个最小可见 Qt 窗口就可能让 ``TOTAL resident`` 到 400 MB
量级。这里大头通常是共享或文件映射的系统库页面，例如 AppKit、WebKit、JavaScriptCore
和 libobjc。它们不等价于 FeelUOwn 自己的 Python heap，也不直接说明应用发生泄漏。

判读内存指标时优先区分：

- ``Physical footprint``：更接近进程对系统物理内存压力的口径。
- ``Writable resident``：进程可写且已驻留的内存，更适合观察应用私有增长。
- ``TOTAL resident``：包含大量共享库和文件映射页面，适合排查加载了哪些库，但不应单独作为
  “应用私有内存很高”的证据。

只有当 FeelUOwn 相比最小 Qt baseline 有稳定增量，或者长时间运行后 ``Physical footprint`` /
``Writable resident`` / Memray 中的分配持续增长时，才继续追具体模块。

推荐命令
--------

不把 Memray 加进项目依赖，避免影响不支持的平台。调试时用 ``uv --with`` 临时安装：

.. code-block:: bash

   uv run --with memray \
     memray run --native --follow-fork -o /tmp/fuo-memory.bin \
     -m feeluown --debug

复现完成后退出 FeelUOwn，然后生成报告：

.. code-block:: bash

   uv run --with memray memray flamegraph /tmp/fuo-memory.bin
   uv run --with memray memray table /tmp/fuo-memory.bin

如果要分析已经运行的进程，可以用 attach：

.. code-block:: bash

   uv run --with memray memray attach -o /tmp/fuo-memory-attach.bin <pid>

复现场景
--------

建议先固定一组动作，重复 10 到 30 次：

- 首页刷新、搜索、进入专辑 / 歌手 / 播放列表页面。
- 连续切歌、播放失败后找备用资源、打开 / 关闭 MV 或视频窗口。
- 登录、切换 provider、打开设置或网络状态弹窗。
- 长时间静置，确认没有操作时 RSS 是否继续增长。

判读方式
--------

- Flamegraph 顶部如果集中在 FeelUOwn 的 Python 模块，优先检查对应页面、模型、缓存或信号连接。
- 如果集中在 PyQt6、QtWebEngine、mpv 或其它 C 扩展，先缩小到具体操作路径，再考虑 native 工具。
- 如果 table/stats 里大量出现 ``ssl_wrap_socket``、``create_default_context`` 或 HTTP client
  栈，先检查启动阶段是否有自动登录、版本检查、AI 推荐、封面加载等无用户操作的网络请求。
  对非必要请求优先改成懒加载或用户触发。
- 如果 ``--follow-fork`` 下出现 QtWebEngine 子进程占用明显增长，重点看内置浏览器或 WebEngine 页面。
- 如果 Memray 报告不显示明显增长，但系统 RSS 增长，继续用系统工具确认是否是映射文件、
  图形资源、播放器缓冲或外部进程。

系统工具补充
------------

- macOS：Activity Monitor 观察 RSS；需要 native 细节时用 Instruments Allocations，
  或用 ``leaks <pid>`` 做一次性检查。
- Linux：可补充 ``heaptrack`` 或 ``valgrind --tool=massif``。
- QtWebEngine：它可能启动子进程，需要同时观察子进程 RSS。
- mpv：播放、切歌、视频窗口相关增长，优先隔离 mpv 和视频渲染路径。

记录模板
--------

.. code-block:: text

   启动命令:
   系统 / Python / Qt:
   插件:
   复现步骤:
   Memray 输出文件:
   RSS 起点 / 终点:
   报告中排名靠前的分配:
   是否涉及 QtWebEngine 子进程:
   结论:
